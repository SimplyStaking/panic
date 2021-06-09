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
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __spreadArray = (this && this.__spreadArray) || function (to, from) {
    for (var i = 0, il = from.length, j = to.length; i < il; i++, j++)
        to[j] = from[i];
    return to;
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
var files_1 = require("./server/files");
var path_1 = __importDefault(require("path"));
var https_1 = __importDefault(require("https"));
var types_1 = require("./server/types");
var errors_1 = require("./server/errors");
var utils_1 = require("./server/utils");
var express_1 = __importDefault(require("express"));
var body_parser_1 = __importDefault(require("body-parser"));
var cookie_parser_1 = __importDefault(require("cookie-parser"));
var redis_1 = require("./server/redis");
var mongo_1 = require("./server/mongo");
// Import certificate files
var httpsKey = files_1.readFile(path_1.default.join(__dirname, '../../', 'certificates', 'key.pem'));
var httpsCert = files_1.readFile(path_1.default.join(__dirname, '../../', 'certificates', 'cert.pem'));
var httpsOptions = {
    key: httpsKey,
    cert: httpsCert,
};
// Server configuration
var app = express_1.default();
app.disable('x-powered-by');
app.use(express_1.default.json());
app.use(express_1.default.static(path_1.default.join(__dirname, '../', 'build')));
app.use(body_parser_1.default.json());
app.use(cookie_parser_1.default());
app.use(function (err, req, res, next) {
    // This check makes sure this is a JSON parsing issue, but it might be
    // coming from any middleware, not just body-parser.
    if (err instanceof SyntaxError && 'body' in err) {
        console.error(err);
        return res.sendStatus(utils_1.ERR_STATUS); // Bad request
    }
    next();
});
// Connect with Redis
var redisHost = process.env.REDIS_IP || "localhost";
var redisPort = parseInt(process.env.REDIS_PORT || "6379");
var redisDB = parseInt(process.env.REDIS_DB || "10");
var uniqueAlerterIdentifier = process.env.UNIQUE_ALERTER_IDENTIFIER || "";
var redisInterface = new redis_1.RedisInterface(redisHost, redisPort, redisDB);
redisInterface.connect();
// Check the redis connection every 3 seconds. If the connection was dropped,
// re-connect.
setInterval(function () {
    redisInterface.connect();
}, 3000);
// Connect with Mongo
var mongoHost = process.env.DB_IP || "localhost";
var mongoPort = parseInt(process.env.DB_PORT || "27017");
var mongoDB = process.env.DB_NAME || "panicdb";
var mongoOptions = {
    useNewUrlParser: true,
    useUnifiedTopology: true,
    socketTimeoutMS: 10000,
    connectTimeoutMS: 10000,
    serverSelectionTimeoutMS: 5000,
};
var mongoInterface = new mongo_1.MongoInterface(mongoOptions, mongoHost, mongoPort);
(function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, mongoInterface.connect()];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}); })();
// Check the mongo connection every 3 seconds. If the connection was dropped,
// re-connect.
setInterval(function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, mongoInterface.connect()];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}); }, 3000);
// ---------------------------------------- Redis Endpoints
// This endpoint expects a list of base chains (Cosmos, Substrate, or General)
// inside the body structure.
app.post('/server/redis/monitorablesInfo', function (req, res) { return __awaiter(void 0, void 0, void 0, function () {
    var baseChains, missingKeysList, err, invalidBaseChains, err, invalidBaseChains, err, baseChainKeys, baseChainKeysNamespace, baseChainKeysPostfix, constructedKeys, result, err;
    return __generator(this, function (_a) {
        console.log('Received POST request for %s', req.url);
        baseChains = req.body.baseChains;
        missingKeysList = utils_1.missingValues({ baseChains: baseChains });
        if (missingKeysList.length !== 0) {
            err = new (errors_1.MissingKeysInBody.bind.apply(errors_1.MissingKeysInBody, __spreadArray([void 0], missingKeysList)))();
            res.status(err.code).send(utils_1.errorJson(err.message));
            return [2 /*return*/];
        }
        // Check if the passed base chains are valid
        if (Array.isArray(baseChains)) {
            if (!utils_1.allElementsInList(baseChains, redis_1.baseChainsRedis)) {
                invalidBaseChains = utils_1.getElementsNotInList(baseChains, redis_1.baseChainsRedis);
                err = new (errors_1.InvalidBaseChains.bind.apply(errors_1.InvalidBaseChains, __spreadArray([void 0], invalidBaseChains)))();
                res.status(err.code).send(utils_1.errorJson(err.message));
                return [2 /*return*/];
            }
        }
        else {
            invalidBaseChains = utils_1.getElementsNotInList([baseChains], redis_1.baseChainsRedis);
            err = new (errors_1.InvalidBaseChains.bind.apply(errors_1.InvalidBaseChains, __spreadArray([void 0], invalidBaseChains)))();
            res.status(err.code).send(utils_1.errorJson(err.message));
            return [2 /*return*/];
        }
        baseChainKeys = redis_1.getBaseChainKeys();
        baseChainKeysNamespace = redis_1.addPrefixToKeys(baseChainKeys, uniqueAlerterIdentifier + ":");
        baseChainKeysPostfix = redis_1.addPostfixToKeys(baseChainKeysNamespace, '_');
        constructedKeys = baseChains.map(function (baseChain) {
            return baseChainKeysPostfix.monitorables_info + baseChain;
        });
        result = utils_1.resultJson({});
        if (redisInterface.client) {
            redisInterface.client.mget(constructedKeys, function (err, values) {
                if (err) {
                    console.error(err);
                    var retrievalErr = new errors_1.CouldNotRetrieveDataFromRedis();
                    res.status(retrievalErr.code).send(utils_1.errorJson(retrievalErr.message));
                    return;
                }
                baseChains.forEach(function (baseChain, i) {
                    result.result[baseChain] = JSON.parse(values[i]);
                });
                res.status(utils_1.SUCCESS_STATUS).send(result);
                return;
            });
        }
        else {
            err = new errors_1.RedisClientNotInitialised();
            res.status(err.code).send(utils_1.errorJson(err.message));
            return [2 /*return*/];
        }
        return [2 /*return*/];
    });
}); });
// This endpoint expects a list of parent ids inside the body structure.
app.post('/server/redis/alertsOverview', function (req, res) { return __awaiter(void 0, void 0, void 0, function () {
    var parentIds, missingKeysList, err, err, parentHashKeys, parentHashId, redisHashes, redisHashesNamespace, redisHashesPostfix, alertKeysSystem, alertKeysSystemPostfix, alertKeysRepo, alertKeysRepoPostfix, _loop_1, _i, _a, _b, parentId, sourcesObject, result, redisMulti, _loop_2, _c, _d, _e, parentHash, monitorableKeysObject, err;
    return __generator(this, function (_f) {
        console.log('Received POST request for %s', req.url);
        parentIds = req.body.parentIds;
        missingKeysList = utils_1.missingValues({ parentIds: parentIds });
        if (missingKeysList.length !== 0) {
            err = new (errors_1.MissingKeysInBody.bind.apply(errors_1.MissingKeysInBody, __spreadArray([void 0], missingKeysList)))();
            res.status(err.code).send(utils_1.errorJson(err.message));
            return [2 /*return*/];
        }
        // Check if the passed dict is valid
        if (!types_1.isAlertsOverviewInput(parentIds)) {
            err = new errors_1.InvalidJsonSchema("req.body.parentIds");
            res.status(err.code).send(utils_1.errorJson(err.message));
            return [2 /*return*/];
        }
        parentHashKeys = {};
        parentHashId = {};
        redisHashes = redis_1.getRedisHashes();
        redisHashesNamespace = redis_1.addPrefixToKeys(redisHashes, uniqueAlerterIdentifier + ":");
        redisHashesPostfix = redis_1.addPostfixToKeys(redisHashesNamespace, '_');
        alertKeysSystem = redis_1.getAlertKeysSystem();
        alertKeysSystemPostfix = redis_1.addPostfixToKeys(alertKeysSystem, '_');
        alertKeysRepo = redis_1.getAlertKeysRepo();
        alertKeysRepoPostfix = redis_1.addPostfixToKeys(alertKeysRepo, '_');
        _loop_1 = function (parentId, sourcesObject) {
            var parentHash = redisHashesPostfix.parent + parentId;
            parentHashKeys[parentHash] = {};
            parentHashId[parentHash] = parentId;
            sourcesObject.systems.forEach(function (systemId) {
                var constructedKeys = redis_1.addPostfixToKeys(alertKeysSystemPostfix, systemId);
                parentHashKeys[parentHash][systemId] = Object.values(constructedKeys);
            });
            sourcesObject.repos.forEach(function (repoId) {
                var constructedKeys = redis_1.addPostfixToKeys(alertKeysRepoPostfix, repoId);
                parentHashKeys[parentHash][repoId] = Object.values(constructedKeys);
            });
        };
        for (_i = 0, _a = Object.entries(parentIds); _i < _a.length; _i++) {
            _b = _a[_i], parentId = _b[0], sourcesObject = _b[1];
            _loop_1(parentId, sourcesObject);
        }
        result = utils_1.resultJson({});
        if (redisInterface.client) {
            redisMulti = redisInterface.client.multi();
            _loop_2 = function (parentHash, monitorableKeysObject) {
                var parentId = parentHashId[parentHash];
                result.result[parentId] = {
                    "info": 0,
                    "critical": 0,
                    "warning": 0,
                    "error": 0,
                    "problems": {},
                    "releases": {},
                };
                var _loop_3 = function (monitorableId, keysList) {
                    redisMulti.hmget(parentHash, keysList, function (err, values) {
                        if (err) {
                            return;
                        }
                        keysList.forEach(function (key, i) {
                            var value = JSON.parse(values[i]);
                            if (value && value.constructor === Object &&
                                "message" in value && "severity" in value) {
                                // Add array of problems if not initialised
                                // yet and there is indeed problems.
                                if (value.severity !== utils_1.Severities.INFO &&
                                    !result.result[parentId].problems[monitorableId]) {
                                    result.result[parentId].problems[monitorableId] = [];
                                }
                                // If the alerter has detected a new release
                                // add it to the list of releases
                                var newReleaseKey = redis_1.addPostfixToKeys(alertKeysRepoPostfix, monitorableId).github_release;
                                if (key === newReleaseKey) {
                                    result.result[parentId].releases[monitorableId] = value;
                                }
                                // Increase the counter and save the
                                // problems.
                                if (value.severity === utils_1.Severities.INFO) {
                                    result.result[parentId].info += 1;
                                }
                                else if (value.severity === utils_1.Severities.CRITICAL) {
                                    result.result[parentId].critical += 1;
                                    result.result[parentId].problems[monitorableId].push(value);
                                }
                                else if (value.severity === utils_1.Severities.WARNING) {
                                    result.result[parentId].warning += 1;
                                    result.result[parentId].problems[monitorableId].push(value);
                                }
                                else if (value.severity === utils_1.Severities.ERROR) {
                                    result.result[parentId].error += 1;
                                    result.result[parentId].problems[monitorableId].push(value);
                                }
                            }
                            else {
                                result.result[parentId].info += 1;
                            }
                        });
                    });
                };
                for (var _g = 0, _h = Object.entries(monitorableKeysObject); _g < _h.length; _g++) {
                    var _j = _h[_g], monitorableId = _j[0], keysList = _j[1];
                    _loop_3(monitorableId, keysList);
                }
            };
            for (_c = 0, _d = Object.entries(parentHashKeys); _c < _d.length; _c++) {
                _e = _d[_c], parentHash = _e[0], monitorableKeysObject = _e[1];
                _loop_2(parentHash, monitorableKeysObject);
            }
            redisMulti.exec(function (err, _) {
                if (err) {
                    console.error(err);
                    var retrievalErr = new errors_1.CouldNotRetrieveDataFromRedis();
                    res.status(retrievalErr.code).send(utils_1.errorJson(retrievalErr.message));
                    return;
                }
                res.status(utils_1.SUCCESS_STATUS).send(result);
                return;
            });
        }
        else {
            err = new errors_1.RedisClientNotInitialised();
            res.status(err.code).send(utils_1.errorJson(err.message));
            return [2 /*return*/];
        }
        return [2 /*return*/];
    });
}); });
// ---------------------------------------- Mongo Endpoints
app.post('/server/mongo/alerts', function (req, res) { return __awaiter(void 0, void 0, void 0, function () {
    var _a, chains, severities, sources, minTimestamp, maxTimestamp, noOfAlerts, missingKeysList, err, arrayBasedStringParams, _i, _b, _c, param, value, err, _d, severities_1, severity, err, positiveFloats, _e, _f, _g, param, value, parsedFloat, err, parsedMinTimestamp, parsedMaxTimestamp, parsedNoOfAlerts, err, result, db, queryList, i, collection, docs, _h, docs_1, doc, err_1, retrievalErr, err;
    return __generator(this, function (_j) {
        switch (_j.label) {
            case 0:
                console.log('Received POST request for %s', req.url);
                _a = req.body, chains = _a.chains, severities = _a.severities, sources = _a.sources, minTimestamp = _a.minTimestamp, maxTimestamp = _a.maxTimestamp, noOfAlerts = _a.noOfAlerts;
                missingKeysList = utils_1.missingValues({
                    chains: chains,
                    severities: severities,
                    sources: sources,
                    minTimestamp: minTimestamp,
                    maxTimestamp: maxTimestamp,
                    noOfAlerts: noOfAlerts
                });
                if (missingKeysList.length !== 0) {
                    err = new (errors_1.MissingKeysInBody.bind.apply(errors_1.MissingKeysInBody, __spreadArray([void 0], missingKeysList)))();
                    res.status(err.code).send(utils_1.errorJson(err.message));
                    return [2 /*return*/];
                }
                arrayBasedStringParams = { chains: chains, severities: severities, sources: sources };
                for (_i = 0, _b = Object.entries(arrayBasedStringParams); _i < _b.length; _i++) {
                    _c = _b[_i], param = _c[0], value = _c[1];
                    if (!Array.isArray(value) ||
                        !utils_1.allElementsInListHaveTypeString(value)) {
                        err = new errors_1.InvalidParameterValue("req.body." + param);
                        res.status(err.code).send(utils_1.errorJson(err.message));
                        return [2 /*return*/];
                    }
                }
                for (_d = 0, severities_1 = severities; _d < severities_1.length; _d++) {
                    severity = severities_1[_d];
                    if (!(severity in utils_1.Severities)) {
                        err = new errors_1.InvalidParameterValue("req.body.severities");
                        res.status(err.code).send(utils_1.errorJson(err.message));
                        return [2 /*return*/];
                    }
                }
                positiveFloats = { minTimestamp: minTimestamp, maxTimestamp: maxTimestamp };
                for (_e = 0, _f = Object.entries(positiveFloats); _e < _f.length; _e++) {
                    _g = _f[_e], param = _g[0], value = _g[1];
                    parsedFloat = parseFloat(value);
                    if (isNaN(parsedFloat) || parsedFloat < 0) {
                        err = new errors_1.InvalidParameterValue("req.body." + param);
                        res.status(err.code).send(utils_1.errorJson(err.message));
                        return [2 /*return*/];
                    }
                }
                parsedMinTimestamp = parseFloat(minTimestamp);
                parsedMaxTimestamp = parseFloat(maxTimestamp);
                parsedNoOfAlerts = parseInt(noOfAlerts);
                if (isNaN(parsedNoOfAlerts) || parsedNoOfAlerts <= 0) {
                    err = new errors_1.InvalidParameterValue('req.body.noOfAlerts');
                    res.status(err.code).send(utils_1.errorJson(err.message));
                    return [2 /*return*/];
                }
                result = utils_1.resultJson({ alerts: [] });
                if (!mongoInterface.client) return [3 /*break*/, 6];
                _j.label = 1;
            case 1:
                _j.trys.push([1, 4, , 5]);
                db = mongoInterface.client.db(mongoDB);
                if (!(chains.length > 0)) return [3 /*break*/, 3];
                queryList = [];
                for (i = 1; i < chains.length; i++) {
                    queryList.push({ $unionWith: chains[i] });
                }
                queryList.push({ $match: { doc_type: "alert" } }, { $unwind: "$alerts" }, {
                    $match: {
                        "alerts.severity": { $in: severities },
                        "alerts.origin": { $in: sources },
                        "alerts.timestamp": {
                            "$gte": parsedMinTimestamp,
                            "$lte": parsedMaxTimestamp
                        }
                    }
                }, { $sort: { "alerts.timestamp": -1, _id: 1 } }, { $limit: parsedNoOfAlerts }, { $group: { _id: null, alrts: { $push: "$alerts" } } }, { $project: { _id: 0, alerts: "$alrts" } });
                collection = db.collection(chains[0]);
                return [4 /*yield*/, collection.aggregate(queryList)
                        .toArray()];
            case 2:
                docs = _j.sent();
                for (_h = 0, docs_1 = docs; _h < docs_1.length; _h++) {
                    doc = docs_1[_h];
                    result.result.alerts = result.result.alerts.concat(doc.alerts);
                }
                _j.label = 3;
            case 3:
                console.log(result.result.alerts.length);
                res.status(utils_1.SUCCESS_STATUS).send(result);
                return [2 /*return*/];
            case 4:
                err_1 = _j.sent();
                console.error(err_1);
                retrievalErr = new errors_1.CouldNotRetrieveDataFromMongo();
                res.status(retrievalErr.code).send(utils_1.errorJson(retrievalErr.message));
                return [2 /*return*/];
            case 5: return [3 /*break*/, 7];
            case 6:
                err = new errors_1.MongoClientNotInitialised();
                res.status(err.code).send(utils_1.errorJson(err.message));
                return [2 /*return*/];
            case 7: return [2 /*return*/];
        }
    });
}); });
// ---------------------------------------- Server defaults
app.get('/server/*', function (req, res) { return __awaiter(void 0, void 0, void 0, function () {
    var err;
    return __generator(this, function (_a) {
        console.log('Received GET request for %s', req.url);
        err = new errors_1.InvalidEndpoint(req.url);
        res.status(err.code).send(utils_1.errorJson(err.message));
        return [2 /*return*/];
    });
}); });
app.post('/server/*', function (req, res) { return __awaiter(void 0, void 0, void 0, function () {
    var err;
    return __generator(this, function (_a) {
        console.log('Received POST request for %s', req.url);
        err = new errors_1.InvalidEndpoint(req.url);
        res.status(err.code).send(utils_1.errorJson(err.message));
        return [2 /*return*/];
    });
}); });
// ---------------------------------------- PANIC UI
// Return the build at the root URL
app.get('/*', function (req, res) {
    console.log('Received GET request for %s', req.url);
    res.sendFile(path_1.default.join(__dirname, 'build', 'index.html'));
});
// ---------------------------------------- Start listen
var port = parseInt(process.env.UI_API_PORT || "9000");
// Create Https server
var server = https_1.default.createServer(httpsOptions, app);
// Listen for requests
server.listen(port, function () { return console.log('Listening on %s', port); });
// TODO: Need to add authentication, even to the respective middleware functions
