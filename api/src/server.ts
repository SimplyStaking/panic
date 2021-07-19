import * as dotenv from "dotenv";
import { readFile } from "./server/files";
import path from "path";
import https from "https";
import {
    AlertKeysGitHubRepo,
    AlertKeysSystem,
    AlertsOverviewInput,
    ParentSourceInput,
    AlertsOverviewResult,
    BaseChainKeys,
    HttpsOptions,
    isAlertsOverviewInput,
    isParentSourceInput,
    MonitorablesInfoResult,
    RedisHashes,
    RedisKeys,
    SystemKeys,
    GitHubKeys,
    MetricsResult
} from "./server/types";
import {
    CouldNotRetrieveDataFromMongo,
    CouldNotRetrieveDataFromRedis,
    InvalidBaseChains,
    InvalidEndpoint,
    InvalidJsonSchema,
    InvalidParameterValue,
    MissingKeysInBody,
    MongoClientNotInitialised,
    RedisClientNotInitialised
} from './server/errors'
import {
    allElementsInList,
    allElementsInListHaveTypeString,
    errorJson,
    getElementsNotInList,
    missingValues,
    resultJson,
} from "./server/utils";
import express from "express";
import bodyParser from "body-parser";
import cookieParser from "cookie-parser";
import {
    addPostfixToKeys,
    addPrefixToKeys,
    baseChainsRedis,
    getAlertKeysGitHubRepo,
    getAlertKeysSystem,
    getBaseChainKeys,
    getRedisHashes,
    RedisInterface,
    getSystemKeys,
    getGitHubKeys,
    getChainlinkKeys
} from "./server/redis"
import {MongoInterface} from "./server/mongo";
import {MongoClientOptions} from "mongodb";
import { ERR_STATUS, Severities, SUCCESS_STATUS } from "./server/constants";
import { stringify } from "querystring";
const swaggerUi = require('swagger-ui-express');
const swaggerDocument = require('./swagger.json');

// Use the environmental variables from the .env file
dotenv.config();

// Import certificate files
const httpsKey: Buffer = readFile(path.join(__dirname, '../../', 'certificates',
    'key.pem'));
const httpsCert: Buffer = readFile(path.join(__dirname, '../../',
    'certificates', 'cert.pem'));
const httpsOptions: HttpsOptions = {
    key: httpsKey,
    cert: httpsCert,
};

// Server configuration
const app = express();
app.disable('x-powered-by');
app.use(express.json());
app.use(express.static(path.join(__dirname, '../', 'build')));
app.use(bodyParser.json());
app.use(cookieParser());
app.use((err: any, req: express.Request, res: express.Response,
         next: express.NextFunction) => {
    // This check makes sure this is a JSON parsing issue, but it might be
    // coming from any middleware, not just body-parser.
    if (err instanceof SyntaxError && 'body' in err) {
        console.error(err);
        return res.sendStatus(ERR_STATUS); // Bad request
    }

    next();
});
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));

// Connect with Redis
const redisHost = process.env.REDIS_IP || "localhost";
const redisPort = parseInt(process.env.REDIS_PORT || "6379");
const redisDB = parseInt(process.env.REDIS_DB || "10");
const uniqueAlerterIdentifier = process.env.UNIQUE_ALERTER_IDENTIFIER || "";
const redisInterface = new RedisInterface(redisHost, redisPort, redisDB);
redisInterface.connect();

// Check the redis connection every 3 seconds. If the connection was dropped,
// re-connect.
setInterval(() => {
    redisInterface.connect();
}, 3000);

// Connect with Mongo
const mongoHost = process.env.DB_IP || "localhost";
const mongoPort = parseInt(process.env.DB_PORT || "27017");
const mongoDB = process.env.DB_NAME || "panicdb";
const mongoOptions: MongoClientOptions = {
    useNewUrlParser: true,
    useUnifiedTopology: true,
    socketTimeoutMS: 10000,
    connectTimeoutMS: 10000,
    serverSelectionTimeoutMS: 5000,
};
const mongoInterface = new MongoInterface(mongoOptions, mongoHost, mongoPort);
(async () => {
    await mongoInterface.connect();
})();

// Check the mongo connection every 3 seconds. If the connection was dropped,
// re-connect.
setInterval(async () => {
    await mongoInterface.connect();
}, 3000);

// ---------------------------------------- Redis Endpoints

// This endpoint expects a list of base chains (cosmos, substrate, chainlink or general)
// inside the body structure.
app.post('/server/redis/monitorablesInfo',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const {baseChains} = req.body;

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({baseChains});
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // Check if the passed base chains are valid
        if (Array.isArray(baseChains)) {
            if (!allElementsInList(baseChains, baseChainsRedis)) {
                const invalidBaseChains: string[] = getElementsNotInList(
                    baseChains, baseChainsRedis);
                const err = new InvalidBaseChains(...invalidBaseChains);
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        } else {
            const invalidBaseChains: any[] = getElementsNotInList([baseChains],
                baseChainsRedis);
            const err = new InvalidBaseChains(...invalidBaseChains);
            res.status(err.code).send(errorJson(err.message));
            return;
        }
        // Construct the redis keys
        const baseChainKeys: BaseChainKeys = getBaseChainKeys();
        const baseChainKeysNamespace: RedisKeys = addPrefixToKeys(
            baseChainKeys, `${uniqueAlerterIdentifier}:`);
        const baseChainKeysPostfix: RedisKeys = addPostfixToKeys(
            baseChainKeysNamespace, '_');
        let constructedKeys: string[] = baseChains.map(
            (baseChain: string): string => {
                return baseChainKeysPostfix.monitorables_info + baseChain
            });
        let result: MonitorablesInfoResult = resultJson({});
        if (redisInterface.client) {
            redisInterface.client.mget(constructedKeys, (err: any, values: any) => {
                if (err) {
                    console.error(err);
                    const retrievalErr = new CouldNotRetrieveDataFromRedis();
                    res.status(retrievalErr.code).send(errorJson(
                        retrievalErr.message));
                    return
                }
                baseChains.forEach(
                    (baseChain: string, i: number): void => {
                        result.result[baseChain] = JSON.parse(values[i])
                    });
                res.status(SUCCESS_STATUS).send(result);
                return;
            });
        } else {
            // This is done just for the case of completion, as it is very
            // unlikely to occur.
            const err = new RedisClientNotInitialised();
            res.status(err.code).send(errorJson(err.message));
            return;
        }
    });

// This endpoint expects a list of parent ids inside the body structure.
app.post('/server/redis/alertsOverview',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s', req.url);
        const parentIds: AlertsOverviewInput = req.body.parentIds;
        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({parentIds});
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // Check if the passed dict is valid
        if (!isAlertsOverviewInput(parentIds)) {
            const err = new InvalidJsonSchema("req.body.parentIds");
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // Construct the redis keys inside a JSON object indexed by parent hash
        // and the system/repo id. We also need a way to map the hash to the
        // parent id.
        const parentHashKeys: { [key: string]: { [key: string]: string[] } } = {};
        const parentHashId: { [key: string]: string } = {};

        const redisHashes: RedisHashes = getRedisHashes();
        const redisHashesNamespace: RedisKeys = addPrefixToKeys(
            redisHashes, `${uniqueAlerterIdentifier}:`);
        const redisHashesPostfix: RedisKeys = addPostfixToKeys(
            redisHashesNamespace, '_');
        const alertKeysSystem: AlertKeysSystem = getAlertKeysSystem();
        const alertKeysSystemPostfix: RedisKeys = addPostfixToKeys(
            alertKeysSystem, '_');
        const alertKeysRepo: AlertKeysGitHubRepo = getAlertKeysGitHubRepo();
        const alertKeysRepoPostfix: RedisKeys = addPostfixToKeys(alertKeysRepo,
            '_');
        for (const [parentId, sourcesObject] of Object.entries(parentIds)) {
            const parentHash: string = redisHashesPostfix.parent + parentId;
            parentHashKeys[parentHash] = {};
            parentHashId[parentHash] = parentId;
            sourcesObject.systems.forEach((systemId) => {
                const constructedKeys: RedisKeys = addPostfixToKeys(
                    alertKeysSystemPostfix, systemId);
                parentHashKeys[parentHash][systemId] = Object.values(
                    constructedKeys)
            });
            sourcesObject.repos.forEach((repoId) => {
                const constructedKeys: RedisKeys = addPostfixToKeys(
                    alertKeysRepoPostfix, repoId);
                parentHashKeys[parentHash][repoId] = Object.values(
                    constructedKeys)
            });
        }

        let result: AlertsOverviewResult = resultJson({});
        if (redisInterface.client) {
            // Using multi() means that all commands are only performed once
            // exec() is called, and this is done atomically.
            const redisMulti = redisInterface.client.multi();
            for (const [parentHash, monitorableKeysObject] of Object.entries(
                parentHashKeys)) {
                const parentId: string = parentHashId[parentHash];
                const currentTimestamp = Math.floor(Date.now() / 1000);
                result.result[parentId] = {
                    "info": 0,
                    "critical": 0,
                    "warning": 0,
                    "error": 0,
                    "problems": {},
                    "releases": {},
                };
                for (const [monitorableId, keysList] of
                    Object.entries(monitorableKeysObject)) {
                    redisMulti.hmget(parentHash, keysList, (err: any, values: any) => {
                        if (err) {
                            console.log(err);
                            return
                        }
                        keysList.forEach(
                            (key: string, i: number): void => {
                                const value = JSON.parse(values[i]);
                                if (value && value.constructor === Object &&
                                    "message" in value && "severity" in value
                                      && "expiry" in value) {
                                    // Add array of problems if not initialised
                                    // yet and there is indeed problems.
                                    if (value.severity !== Severities.INFO &&
                                        !result.result[parentId].problems[monitorableId] &&
                                        !(currentTimestamp >= value.expiry)) {
                                        result.result[parentId].problems[
                                            monitorableId] = []
                                    }
                                    // If the alerter has detected a new release
                                    // add it to the list of releases
                                    const newReleaseKey: string =
                                        addPostfixToKeys(
                                            alertKeysRepoPostfix,
                                            monitorableId).github_release;
                                    if (key === newReleaseKey) {
                                        result.result[parentId].releases[
                                            monitorableId] = value
                                    }
                                    if (currentTimestamp >= value.expiry){
                                      result.result[parentId].info += 1;
                                    }else{
                                      // Increase the counter and save the
                                      // problems.
                                      if (value.severity === Severities.INFO) {
                                        result.result[parentId].info += 1;
                                      } else if (
                                          value.severity === Severities.CRITICAL
                                      ) {
                                          result.result[parentId].critical += 1;
                                          result.result[parentId].problems[
                                              monitorableId].push(value)
                                      } else if (
                                          value.severity === Severities.WARNING
                                      ) {
                                          result.result[parentId].warning += 1;
                                          result.result[parentId].problems[
                                              monitorableId].push(value)
                                      } else if (
                                          value.severity === Severities.ERROR
                                      ) {
                                          result.result[parentId].error += 1;
                                          result.result[parentId].problems[
                                              monitorableId].push(value)
                                      }
                                    }
                                } else {
                                    result.result[parentId].info += 1;
                                }
                            });
                    })
                }
            }
            redisMulti.exec((err: any, _: any) => {
                if (err) {
                    console.error(err);
                    const retrievalErr = new CouldNotRetrieveDataFromRedis();
                    res.status(retrievalErr.code).send(errorJson(
                        retrievalErr.message));
                    return
                }
                res.status(SUCCESS_STATUS).send(result);
                return;
            });
        } else {
            // This is done just for the sake of completion, as it is very
            // unlikely to occur.
            const err = new RedisClientNotInitialised();
            res.status(err.code).send(errorJson(err.message));
            return;
        }
    });

// This endpoint returns metrics and their values, for the requested sources
// and their chains
app.post('/server/redis/metrics',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s', req.url);
        const parentIds: ParentSourceInput = req.body.parentIds;

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({parentIds});
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // Check if the passed dict is valid
        if (!isParentSourceInput(parentIds)) {
            const err = new InvalidJsonSchema("req.body.parentIds");
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // Construct the redis keys inside a JSON object indexed by parent hash
        // and the system/repo id. We also need a way to map the hash to the
        // parent id.
        const parentHashKeys: { [key: string]: { [key: string]: string[] } } = {};
        const parentHashId: { [key: string]: string } = {};

        const redisHashes: RedisHashes = getRedisHashes();
        const redisHashesNamespace: RedisKeys = addPrefixToKeys(
            redisHashes, `${uniqueAlerterIdentifier}:`);
        const redisHashesPostfix: RedisKeys = addPostfixToKeys(
            redisHashesNamespace, '_');
        
        const metricKeysSystem: SystemKeys = getSystemKeys();
        const metricKeysSystemPostfix: RedisKeys = addPostfixToKeys(
            metricKeysSystem, '_');
        
        const metricKeysGitHub: GitHubKeys = getGitHubKeys();
        const metricKeysGitHubPostfix: RedisKeys = addPostfixToKeys(
            metricKeysGitHub, '_');

        for (const [parentId, sourcesObject] of Object.entries(parentIds)) {
            const parentHash: string = redisHashesPostfix.parent + parentId;
            parentHashKeys[parentHash] = {};
            parentHashId[parentHash] = parentId;
            sourcesObject.systems.forEach((systemId) => {
                const constructedKeys: RedisKeys = addPostfixToKeys(
                    metricKeysSystemPostfix, systemId);
                parentHashKeys[parentHash][systemId] = Object.values(
                    constructedKeys)
            });
            sourcesObject.repos.forEach((repoId) => {
                const constructedKeys: RedisKeys = addPostfixToKeys(
                    metricKeysGitHubPostfix, repoId);
                parentHashKeys[parentHash][repoId] = Object.values(
                    constructedKeys)
            });
        }

        let result: MetricsResult = resultJson({});
        if (redisInterface.client) {
            // Using multi() means that all commands are only performed once
            // exec() is called, and this is done atomically.
            const redisMulti = redisInterface.client.multi();
            for (const [parentHash, monitorableKeysObject] of Object.entries(
                parentHashKeys)) {
                const parentId: string = parentHashId[parentHash];
                result.result[parentId] = {
                    "system": {},
                    "github": {},
                };
                for (const [monitorableId, keysList] of
                    Object.entries(monitorableKeysObject)) {
                    redisMulti.hmget(parentHash, keysList, (err: any, values: any) => {
                        if (err) {
                            console.log(err);
                            return
                        }
                        keysList.forEach(
                          (key: string, i: number): void => {
                            // Must be stringified as it doesn't parse `None`
                            const value = JSON.parse(JSON.stringify(values[i]));
                            if (monitorableId.includes('system')) {
                              if(!(monitorableId in result.result[parentId].system)){
                                result.result[parentId].system[monitorableId] = <SystemKeys>{}
                              }
                              result.result[parentId].system[monitorableId][key.replace('_' + monitorableId, '')] = value;
                            }else if (monitorableId.includes('repo')){
                              if(!(monitorableId in result.result[parentId].github)){
                                result.result[parentId].github[monitorableId] = <GitHubKeys>{}
                              }
                              result.result[parentId].github[monitorableId][key.replace('_' + monitorableId, '')] = value;
                            }else{
                              // Do nothing
                            }
                          });
                    })
                }
            }
            redisMulti.exec((err: any, _: any) => {
                if (err) {
                    console.error(err);
                    const retrievalErr = new CouldNotRetrieveDataFromRedis();
                    res.status(retrievalErr.code).send(errorJson(
                        retrievalErr.message));
                    return
                }
                res.status(SUCCESS_STATUS).send(result);
                return;
            });
        } else {
            // This is done just for the sake of completion, as it is very
            // unlikely to occur.
            const err = new RedisClientNotInitialised();
            res.status(err.code).send(errorJson(err.message));
            return;
        }
    });

// ---------------------------------------- Mongo Endpoints

app.post('/server/mongo/alerts',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s', req.url);
        const {
            chains,
            severities,
            sources,
            minTimestamp,
            maxTimestamp,
            noOfAlerts
        } = req.body;

        // Check that all parameters have been sent
        const missingKeysList: string[] = missingValues({
            chains,
            severities,
            sources,
            minTimestamp,
            maxTimestamp,
            noOfAlerts
        });
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // --------------------- Input Validation -------------------

        const arrayBasedStringParams = {chains, severities, sources};
        for (const [param, value] of Object.entries(arrayBasedStringParams)) {
            if (!Array.isArray(value) ||
                !allElementsInListHaveTypeString(value)) {
                const err = new InvalidParameterValue(`req.body.${param}`);
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        }

        for (const severity of severities) {
            if (!(severity in Severities)) {
                const err = new InvalidParameterValue('req.body.severities');
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        }

        const positiveFloats = {minTimestamp, maxTimestamp};
        for (const [param, value] of Object.entries(positiveFloats)) {
            const parsedFloat = parseFloat(value);
            if (isNaN(parsedFloat) || parsedFloat < 0) {
                const err = new InvalidParameterValue(`req.body.${param}`);
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        }
        const parsedMinTimestamp = parseFloat(minTimestamp);
        const parsedMaxTimestamp = parseFloat(maxTimestamp);

        const parsedNoOfAlerts = parseInt(noOfAlerts);
        if (isNaN(parsedNoOfAlerts) || parsedNoOfAlerts <= 0) {
            const err = new InvalidParameterValue('req.body.noOfAlerts');
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        let result = resultJson({alerts: []});
        if (mongoInterface.client) {
            try {
                const db = mongoInterface.client.db(mongoDB);
                if (chains.length > 0) {
                    let queryList: any = [];
                    for (let i = 1; i < chains.length; i++) {
                        queryList.push({$unionWith: chains[i]})
                    }
                    queryList.push(
                        {$match: {doc_type: "alert"}},
                        {$unwind: "$alerts"},
                        {
                            $match: {
                                "alerts.severity": {$in: severities},
                                "alerts.origin": {$in: sources},
                                "alerts.timestamp": {
                                    "$gte": parsedMinTimestamp,
                                    "$lte": parsedMaxTimestamp
                                }
                            }
                        },
                        {$sort: {"alerts.timestamp": -1, _id: 1}},
                        {$limit: parsedNoOfAlerts},
                        {$group: {_id: null, alerts: {$push: "$alerts"}}},
                        {$project: {_id: 0, alerts: "$alerts"}},
                    );
                    const collection = db.collection(chains[0]);
                    const docs = await collection.aggregate(queryList)
                        .toArray();
                    for (const doc of docs) {
                        result.result.alerts = result.result.alerts.concat(
                            doc.alerts)
                    }
                }
                res.status(SUCCESS_STATUS).send(result);
                return;
            } catch (err) {
                console.error(err);
                const retrievalErr = new CouldNotRetrieveDataFromMongo();
                res.status(retrievalErr.code).send(errorJson(
                    retrievalErr.message));
                return;
            }
        } else {
            // This is done just for the sake of completion, as it is very
            // unlikely to occur.
            const err = new MongoClientNotInitialised();
            res.status(err.code).send(errorJson(err.message));
            return;
        }
    });

app.post('/server/mongo/metrics',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s', req.url);
        const {
            chains,
            sources,
            minTimestamp,
            maxTimestamp,
            noOfMetricsPerSource
        } = req.body;

        // Check that all parameters have been sent
        const missingKeysList: string[] = missingValues({
            chains,
            sources,
            minTimestamp,
            maxTimestamp,
            noOfMetricsPerSource
        });
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // --------------------- Input Validation -------------------

        const arrayBasedStringParams = {chains, sources};
        for (const [param, value] of Object.entries(arrayBasedStringParams)) {
            if (!Array.isArray(value) ||
                !allElementsInListHaveTypeString(value)) {
                const err = new InvalidParameterValue(`req.body.${param}`);
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        }

        const positiveFloats = {minTimestamp, maxTimestamp};
        for (const [param, value] of Object.entries(positiveFloats)) {
            const parsedFloat = parseFloat(value);
            if (isNaN(parsedFloat) || parsedFloat < 0) {
                const err = new InvalidParameterValue(`req.body.${param}`);
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        }
        const parsedMinTimestamp = parseFloat(minTimestamp);
        const parsedMaxTimestamp = parseFloat(maxTimestamp);

        const parsedNoOfMetricsPerSource = parseInt(noOfMetricsPerSource);
        if (isNaN(parsedNoOfMetricsPerSource) || parsedNoOfMetricsPerSource <= 0) {
            const err = new InvalidParameterValue('req.body.noOfMetricsPerSource');
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        let result = resultJson({metrics: {}});
        if (mongoInterface.client) {
            try {
                const db = mongoInterface.client.db(mongoDB);
                if (chains.length > 0) {
                    var queryPromise = new Promise<void>((resolve, reject) => {
                      sources.forEach(async (source: string, i:number): Promise<void> => {
                        let queryList: any = [];
                        for (let i = 1; i < chains.length; i++) {
                          queryList.push({$unionWith: chains[i]})
                        }

                        if (!(source in result.result.metrics)){
                          result.result.metrics[source] = []
                        }

                        let docType;
                        if(source.includes("system")){
                          docType = "system"
                        }
                        const originSource = "$".concat(source);
                        const timestampSource = source.concat(".timestamp");
                        queryList.push(
                          {$match: {doc_type: docType}},
                          {$unwind: originSource},
                          {
                            $match: {
                              [timestampSource]: {
                                "$gte": parsedMinTimestamp,
                                "$lte": parsedMaxTimestamp
                              }
                            }
                          },
                          {$sort: {"timestamp": -1, _id: 1}},
                          {$limit: parsedNoOfMetricsPerSource},
                        );
                        const collection = db.collection(chains[0]);
                        const docs = await collection.aggregate(queryList)
                          .toArray();
                        for (const doc of docs) {
                          result.result.metrics[source] = result.result.metrics[source].concat(
                              doc[source])
                        }
                        if (i === sources.length -1) resolve();
                      });
                    });
                    
                    queryPromise.then(() => {
                      res.status(SUCCESS_STATUS).send(result);
                      return;
                    });
                } else {
                  res.status(SUCCESS_STATUS).send(result);
                  return;
                }
            } catch (err) {
                console.error(err);
                const retrievalErr = new CouldNotRetrieveDataFromMongo();
                res.status(retrievalErr.code).send(errorJson(
                    retrievalErr.message));
                return;
            }
        } else {
            // This is done just for the sake of completion, as it is very
            // unlikely to occur.
            const err = new MongoClientNotInitialised();
            res.status(err.code).send(errorJson(err.message));
            return;
        }
    });

// ---------------------------------------- Server defaults

app.get('/server/*', async (req: express.Request, res: express.Response) => {
    console.log('Received GET request for %s', req.url);
    const err: InvalidEndpoint = new InvalidEndpoint(req.url);
    res.status(err.code).send(errorJson(err.message));
});

app.post('/server/*', async (req: express.Request, res: express.Response) => {
    console.log('Received POST request for %s', req.url);
    const err = new InvalidEndpoint(req.url);
    res.status(err.code).send(errorJson(err.message));
});

// ---------------------------------------- PANIC UI

// Return the build at the root URL
app.get('/*', (req: express.Request, res: express.Response) => {
    console.log('Received GET request for %s', req.url);
    res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// ---------------------------------------- Start listen

const port = parseInt(process.env.API_PORT || "9000");
// Create Https server
const server = https.createServer(httpsOptions, app);
// Listen for requests
server.listen(port, () => console.log('Listening on %s', port));

// TODO: Need to add authentication, even to the respective middleware functions
