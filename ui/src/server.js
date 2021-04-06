"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const files_1 = require("./server/files");
const path_1 = __importDefault(require("path"));
const https_1 = __importDefault(require("https"));
const types_1 = require("./server/types");
const errors_1 = require("./server/errors");
const utils_1 = require("./server/utils");
const express_1 = __importDefault(require("express"));
const body_parser_1 = __importDefault(require("body-parser"));
const cookie_parser_1 = __importDefault(require("cookie-parser"));
const redis_1 = require("./server/redis");
// Import certificate files
const httpsKey = files_1.readFile(path_1.default.join(__dirname, '../../', 'certificates', 'key.pem'));
const httpsCert = files_1.readFile(path_1.default.join(__dirname, '../../', 'certificates', 'cert.pem'));
const httpsOptions = {
    key: httpsKey,
    cert: httpsCert,
};
// Server configuration
const app = express_1.default();
app.disable('x-powered-by');
app.use(express_1.default.json());
app.use(express_1.default.static(path_1.default.join(__dirname, '../', 'build')));
app.use(body_parser_1.default.json());
app.use(cookie_parser_1.default());
app.use((err, req, res, next) => {
    // This check makes sure this is a JSON parsing issue, but it might be
    // coming from any middleware, not just body-parser.
    if (err instanceof SyntaxError && 'body' in err) {
        console.error(err);
        return res.sendStatus(utils_1.ERR_STATUS); // Bad request
    }
    next();
});
// Connect with Redis
const redisHost = process.env.REDIS_IP || "localhost";
const redisPort = parseInt(process.env.REDIS_PORT || "6379");
const redisDB = parseInt(process.env.REDIS_DB || "10");
const uniqueAlerterIdentifier = process.env.UNIQUE_ALERTER_IDENTIFIER || "";
const redisInterface = new redis_1.RedisInterface(redisHost, redisPort, redisDB);
redisInterface.connect();
// Check the redis connection every 3 seconds. If the connection was dropped,
// re-connect.
setInterval(() => {
    redisInterface.connect();
}, 3000);
// ---------------------------------------- Redis Endpoints
// This endpoint expects a list of base chains (Cosmos, Substrate, or General)
// inside the body structure.
app.post('/server/redis/monitorablesInfo', (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    console.log('Received POST request for %s', req.url);
    const { baseChains } = req.body;
    // Check if some required keys are missing in the body object, if yes
    // notify the client.
    const missingKeysList = utils_1.missingValues({ baseChains });
    if (missingKeysList.length !== 0) {
        const err = new errors_1.MissingKeysInBody(...missingKeysList);
        res.status(err.code).send(utils_1.errorJson(err.message));
        return;
    }
    // Check if the passed base chains are valid
    if (Array.isArray(baseChains)) {
        if (!utils_1.allElementsInList(baseChains, redis_1.baseChainsRedis)) {
            const invalidBaseChains = utils_1.getElementsNotInList(baseChains, redis_1.baseChainsRedis);
            const err = new errors_1.InvalidBaseChains(...invalidBaseChains);
            res.status(err.code).send(utils_1.errorJson(err.message));
            return;
        }
    }
    else {
        const invalidBaseChains = utils_1.getElementsNotInList([baseChains], redis_1.baseChainsRedis);
        const err = new errors_1.InvalidBaseChains(...invalidBaseChains);
        res.status(err.code).send(utils_1.errorJson(err.message));
        return;
    }
    // Construct the redis keys
    const baseChainKeys = redis_1.getBaseChainKeys();
    const baseChainKeysNamespace = redis_1.addPrefixToKeys(baseChainKeys, `${uniqueAlerterIdentifier}:`);
    const baseChainKeysPostfix = redis_1.addPostfixToKeys(baseChainKeysNamespace, '_');
    const constructedKeys = baseChains.map((baseChain) => {
        return baseChainKeysPostfix.monitorables_info + baseChain;
    });
    let result = utils_1.resultJson({});
    if (redisInterface.client) {
        redisInterface.client.mget(constructedKeys, (err, values) => {
            if (err) {
                console.error(err);
                const retrievalErr = new errors_1.CouldNotRetrieveDataFromRedis();
                res.status(retrievalErr.code).send(utils_1.errorJson(retrievalErr.message));
                return;
            }
            baseChains.forEach((baseChain, i) => {
                result.result[baseChain] = JSON.parse(values[i]);
            });
            res.status(utils_1.SUCCESS_STATUS).send(result);
            return;
        });
    }
    else {
        // This is done just for the case of completion, as it is very
        // unlikely to occur.
        const err = new errors_1.RedisClientNotInitialised();
        res.status(err.code).send(utils_1.errorJson(err.message));
        return;
    }
}));
// This endpoint expects a list of parent ids inside the body structure.
app.post('/server/redis/alertsOverview', (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    console.log('Received POST request for %s', req.url);
    const parentIds = req.body.parentIds;
    // Check if some required keys are missing in the body object, if yes
    // notify the client.
    const missingKeysList = utils_1.missingValues({ parentIds });
    if (missingKeysList.length !== 0) {
        const err = new errors_1.MissingKeysInBody(...missingKeysList);
        res.status(err.code).send(utils_1.errorJson(err.message));
        return;
    }
    // Check if the passed dict is valid
    if (!types_1.isAlertsOverviewInput(parentIds)) {
        const err = new errors_1.InvalidJsonSchema("req.body.parentIds");
        res.status(err.code).send(utils_1.errorJson(err.message));
        return;
    }
    // Construct the redis keys inside a JSON object indexed by parent hash
    // and the system/repo id. We also need a way to map the hash to the
    // parent id.
    const parentHashKeys = {};
    const parentHashId = {};
    const redisHashes = redis_1.getRedisHashes();
    const redisHashesNamespace = redis_1.addPrefixToKeys(redisHashes, `${uniqueAlerterIdentifier}:`);
    const redisHashesPostfix = redis_1.addPostfixToKeys(redisHashesNamespace, '_');
    const alertKeysSystem = redis_1.getAlertKeysSystem();
    const alertKeysSystemPostfix = redis_1.addPostfixToKeys(alertKeysSystem, '_');
    const alertKeysRepo = redis_1.getAlertKeysRepo();
    const alertKeysRepoPostfix = redis_1.addPostfixToKeys(alertKeysRepo, '_');
    for (const [parentId, sourcesObject] of Object.entries(parentIds)) {
        const parentHash = redisHashesPostfix.parent + parentId;
        parentHashKeys[parentHash] = {};
        parentHashId[parentHash] = parentId;
        sourcesObject.systems.forEach((systemId) => {
            const constructedKeys = redis_1.addPostfixToKeys(alertKeysSystemPostfix, systemId);
            parentHashKeys[parentHash][systemId] = Object.values(constructedKeys);
        });
        sourcesObject.repos.forEach((repoId) => {
            const constructedKeys = redis_1.addPostfixToKeys(alertKeysRepoPostfix, repoId);
            parentHashKeys[parentHash][repoId] = Object.values(constructedKeys);
        });
    }
    let result = utils_1.resultJson({});
    if (redisInterface.client) {
        // Using multi() means that all commands are only performed once
        // exec() is called, and this is done atomically.
        const redisMulti = redisInterface.client.multi();
        for (const [parentHash, monitorableKeysObject] of Object.entries(parentHashKeys)) {
            const parentId = parentHashId[parentHash];
            result.result[parentId] = {
                "info": 0,
                "critical": 0,
                "warning": 0,
                "error": 0,
                "problems": {},
                "releases": {},
            };
            for (const [monitorableId, keysList] of Object.entries(monitorableKeysObject)) {
                redisMulti.hmget(parentHash, keysList, (err, values) => {
                    if (err) {
                        return;
                    }
                    keysList.forEach((key, i) => {
                        const value = JSON.parse(values[i]);
                        if (value && value.constructor === Object &&
                            "message" in value && "severity" in value) {
                            // Add array of problems if not initialised
                            // yet and there is indeed problems.
                            if (value.severity !== "INFO" &&
                                !result.result[parentId].problems[monitorableId]) {
                                result.result[parentId].problems[monitorableId] = [];
                            }
                            // If the alerter has detected a new release
                            // add it to the list of releases
                            const newReleaseKey = redis_1.addPostfixToKeys(alertKeysRepoPostfix, monitorableId).github_release;
                            if (key === newReleaseKey) {
                                result.result[parentId].releases[monitorableId] = value;
                            }
                            // Increase the counter and save the
                            // problems.
                            if (value.severity === "INFO") {
                                result.result[parentId].info += 1;
                            }
                            else if (value.severity === "CRITICAL") {
                                result.result[parentId].critical += 1;
                                result.result[parentId].problems[monitorableId].push(value);
                            }
                            else if (value.severity === "WARNING") {
                                result.result[parentId].warning += 1;
                                result.result[parentId].problems[monitorableId].push(value);
                            }
                            else if (value.severity === "ERROR") {
                                result.result[parentId].error += 1;
                                result.result[parentId].problems[monitorableId].push(value);
                            }
                        }
                        else {
                            result.result[parentId].info += 1;
                        }
                    });
                });
            }
        }
        redisMulti.exec((err, _) => {
            if (err) {
                console.error(err);
                const retrievalErr = new errors_1.CouldNotRetrieveDataFromRedis();
                res.status(retrievalErr.code).send(utils_1.errorJson(retrievalErr.message));
                return;
            }
            res.status(utils_1.SUCCESS_STATUS).send(result);
            return;
        });
    }
    else {
        // This is done just for the case of completion, as it is very
        // unlikely to occur.
        const err = new errors_1.RedisClientNotInitialised();
        res.status(err.code).send(utils_1.errorJson(err.message));
        return;
    }
}));
// ---------------------------------------- Server defaults
app.get('/server/*', (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    console.log('Received GET request for %s', req.url);
    const err = new errors_1.InvalidEndpoint(req.url);
    res.status(err.code).send(utils_1.errorJson(err.message));
}));
app.post('/server/*', (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    console.log('Received POST request for %s', req.url);
    const err = new errors_1.InvalidEndpoint(req.url);
    res.status(err.code).send(utils_1.errorJson(err.message));
}));
// ---------------------------------------- PANIC UI
// Return the build at the root URL
app.get('/*', (req, res) => {
    console.log('Received GET request for %s', req.url);
    res.sendFile(path_1.default.join(__dirname, 'build', 'index.html'));
});
// ---------------------------------------- Start listen
const port = parseInt(process.env.UI_DASHBOARD_PORT || "9000");
(() => __awaiter(void 0, void 0, void 0, function* () {
    // Create Https server
    const server = https_1.default.createServer(httpsOptions, app);
    // Listen for requests
    server.listen(port, () => console.log('Listening on %s', port));
}))().catch((err) => console.log(err));
// TODO: Need to add authentication, even to the respective middleware functions
