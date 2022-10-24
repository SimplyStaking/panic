import * as dotenv from "dotenv";
import {readFile} from "./server/files";
import path from "path";
import https from "https";
import {
    AlertKeysDockerHubRepo,
    AlertKeysGitHubRepo,
    AlertKeysNode,
    AlertKeysSystem,
    AlertsOverviewAlertData,
    AlertsOverviewInput,
    AlertsOverviewResult,
    GitHubKeys,
    HttpsOptions,
    isAlertsOverviewInputValid,
    isRedisMetricsInputValid,
    MetricsResult,
    MonitorablesInfoResult,
    RedisHashes,
    RedisKeys,
    RedisMetricsInput,
    SystemKeys
} from "./server/types";
import {
    CouldNotRetrieveDataFromMongo,
    CouldNotRetrieveDataFromRedis,
    EnvVariablesNotAvailable,
    InvalidBaseChains,
    InvalidEndpoint,
    InvalidJsonSchema,
    InvalidParameterValue,
    InvalidValueRetrievedFromRedis,
    MissingKeysInBody,
    MongoClientNotInitialised,
    RedisClientNotInitialised
} from './constant/errors'
import {
    allElementsInList,
    allElementsInListHaveTypeString,
    errorJson,
    fulfillWithTimeLimit,
    getElementsNotInList,
    missingValues,
    resultJson,
    toBool,
    verifyNodeExporterPing,
    verifyPrometheusPing,
} from "./server/utils";
import express from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import {
    addPostfixToKeys,
    addPrefixToKeys,
    alertKeysChainSourced,
    alertKeysChainSourcedWithUniqueIdentifier,
    alertKeysClContractPrefix,
    alertKeysClNodePrefix,
    alertKeysCosmosNodePrefix,
    alertKeysDockerHubPrefix,
    alertKeysEvmNodePrefix,
    alertKeysGitHubPrefix,
    alertKeysSubstrateNodePrefix,
    alertKeysSystemPrefix,
    getAlertKeysDockerHubRepo,
    getAlertKeysGitHubRepo,
    getAlertKeysNode,
    getAlertKeysSystem,
    getGitHubKeys,
    getRedisHashes,
    getSystemKeys,
    RedisInterface
} from "./server/redis"
import {MongoInterface, MonitorablesCollection} from "./server/mongo";
import {MongoClientOptions} from "mongodb";
import {GenericRoute} from "./v1/route/GenericRoute";
import {baseChains, PingStatus, Severities, Status, testAlertMessage, Timeout} from "./constant/server";
import {TimeoutError} from "./constant/server.feedback";
import {MongoConnect} from "./v1/service/MongoConnect";
import {event} from '@pagerduty/pdjs';
import {ConfigRoute} from "./v1/route/ConfigRoute";
import {InstallationRoute} from "./v1/route/InstallationRoute";
import {BaseChainRoute} from "./v1/route/BaseChainRoute";
import {ChannelRoute} from "./v1/route/ChannelRoute";
import {GenericModel} from "./v1/entity/model/GenericModel";
import {SeverityAlertSubconfigModel} from "./v1/entity/model/SeverityAlertSubconfigSchema";
import {BaseChainModel} from "./v1/entity/model/BaseChainModel";
import {Model} from "mongoose";
import {MongooseUtil} from "./util/MongooseUtil";
import {ThresholdAlertSubconfigModel} from "./v1/entity/model/ThresholdAlertSubconfigSchema";
import {TimeWindowAlertSubconfigModel} from "./v1/entity/model/TimeWindowAlertSubconfigSchema";

const axios = require('axios');
const opsgenie = require('opsgenie-sdk');
const twilio = require('twilio');
const {WebClient} = require('@slack/web-api');
const Web3 = require('web3');
const nodemailer = require('nodemailer');
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
app.use(cookieParser());
app.use((err: any, req: express.Request, res: express.Response,
         next: express.NextFunction) => {
    // This check makes sure this is a JSON parsing issue, but it might be
    // coming from any middleware, not just body-parser.
    if (err instanceof SyntaxError && 'body' in err) {
        console.error(err);
        return res.sendStatus(Status.ERROR); // Bad request
    }

    next();
});

//timeout
app.use((req: express.Request, res: express.Response,
         next: express.NextFunction): void => {

    let timeout = Timeout.MAX;
    if (req.query && req.query.timeout) {
        timeout = parseInt(req.query.timeout as string) * 1000;
        if (timeout < Timeout.MIN) {
            timeout = Timeout.MIN;
        }
    }

    res.setTimeout(timeout, () => {
        const error = new TimeoutError();
        next(error);
    });

    next();
});

app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));
const allowedOrigins: string[] = [];

const is_dev_mode = process.env.DEV_MODE && toBool(process.env.DEV_MODE);
if (!process.env.UI_ACCESS_IP && !is_dev_mode) {
    console.error('UI_ACCESS_IP environmental variable not specified,' +
        ' stopping API.');
    process.exit(1);
}

const UI_PORT: string = process.env.UI_DASHBOARD_PORT ?
    process.env.UI_DASHBOARD_PORT : '3333';

allowedOrigins.push(
    `https://${process.env.UI_ACCESS_IP}:${UI_PORT}`);
if (is_dev_mode) {
    console.log('NOTE - Accepting connections from UI Dev Server.')
    allowedOrigins.push(
        `http://localhost:${UI_PORT}`);
        allowedOrigins.push(
            `https://localhost:${UI_PORT}`);
        
}

app.use(cors({origin: allowedOrigins}));

// Connect with Redis
const redisHost = process.env.REDIS_IP || "localhost";
const redisPort = parseInt(process.env.REDIS_PORT || "6379");
const redisDB = parseInt(process.env.REDIS_DB || "10");
const uniqueAlerterIdentifier = process.env.UNIQUE_ALERTER_IDENTIFIER || "";
const redisInterface = new RedisInterface(redisHost, redisPort, redisDB);
redisInterface.connect();

// Check the redis connection every 3 seconds. If the connection was dropped,
// re-connect.
const redisInterval = setInterval(() => {
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

// Check the mongo connection every 3 seconds. If the connection was dropped,
// re-connect.
const mongoInterval = setInterval(async () => {
    await mongoInterface.connect();
}, 3000);

MongoConnect.start().then();

// Populate MongoDB with generics, severity alerts and base chains documents.
// Please note that `SeverityAlertSubconfigModel` shares the `generics` collection with `GenericModel`.
// For this reason in the logic below, `severity_alerts` is dependent on `generics`.
const modelsAndFiles: Array<[Model<any>, string]> = [
    [GenericModel, 'generics'],
    [SeverityAlertSubconfigModel, 'severity_alerts'],
    [ThresholdAlertSubconfigModel, 'threshold_alert'],
    [TimeWindowAlertSubconfigModel, 'time_window_alert'],
    [BaseChainModel, 'base_chains']
];

modelsAndFiles.forEach(async ([model, file]) => {
    await MongooseUtil.populateModel(model, file);
});

// Routes
new InstallationRoute(app);
new GenericRoute(app);
new ConfigRoute(app);
new BaseChainRoute(app);
new ChannelRoute(app);

// ---------------------------------------- Mongo Endpoints

// This endpoint expects a list of base chains (cosmos, substrate, chainlink or
// general) inside the body structure.
app.post('/server/mongo/monitorablesInfo',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const baseChainsInput = req.body['baseChains'];

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({
            baseChains: baseChainsInput
        });
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }
        // Check if the passed base chains are valid
        if (Array.isArray(baseChainsInput)) {
            if (!allElementsInList(baseChainsInput, baseChains)) {
                const invalidBaseChains: string[] = getElementsNotInList(
                    baseChainsInput, baseChains);
                const err = new InvalidBaseChains(...invalidBaseChains);
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        } else {
            const invalidBaseChains: any[] = getElementsNotInList(
                [baseChainsInput], baseChains);
            const err = new InvalidBaseChains(...invalidBaseChains);
            res.status(err.code).send(errorJson(err.message));
            return;
        }
        let result: MonitorablesInfoResult = resultJson({});

        for (const [, baseChain] of Object.entries(baseChainsInput)) {
            result.result[baseChain] = {};
        }

        if (mongoInterface.client) {
            try {
                const db = mongoInterface.client.db(mongoDB);
                if (baseChainsInput.length > 0) {
                    const collection = db.collection(MonitorablesCollection);
                    const query = {_id: {$in: baseChainsInput}};
                    const docs = await collection.find(query).toArray();
                    for (const doc of docs) {
                        const baseChainData: any = result.result[doc._id];
                        delete doc._id;
                        for (const parentID in doc) {
                            const chain = doc[parentID];
                            const chainName = chain.chain_name;
                            baseChainData[chainName] = {
                                parent_id: parentID,
                                monitored: {}
                            };
                            delete chain.chain_name;
                            for (const sourceType in chain) {
                                const monitored = baseChainData[chainName].monitored;
                                const chainSource = chain[sourceType];
                                monitored[sourceType] = [];
                                for (const sourceID in chain[sourceType]) {
                                    monitored[sourceType].push({
                                        [sourceID]: chainSource[sourceID].name
                                    });
                                }
                            }
                        }
                    }
                }
                res.status(Status.SUCCESS).send(result);
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
                const err = new InvalidParameterValue(
                    `req.body.${param}`);
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        }

        for (const severity of severities) {
            if (!(severity in Severities)) {
                const err = new InvalidParameterValue(
                    'req.body.severities');
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        }

        const positiveFloats = {minTimestamp, maxTimestamp};
        for (const [param, value] of Object.entries(positiveFloats)) {
            const parsedFloat = parseFloat(value);
            if (isNaN(parsedFloat) || parsedFloat < 0) {
                const err = new InvalidParameterValue(
                    `req.body.${param}`);
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        }
        const parsedMinTimestamp = parseFloat(minTimestamp);
        const parsedMaxTimestamp = parseFloat(maxTimestamp);

        const parsedNoOfAlerts = parseInt(noOfAlerts);
        if (isNaN(parsedNoOfAlerts) || parsedNoOfAlerts <= 0) {
            const err = new InvalidParameterValue(
                'req.body.noOfAlerts');
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        let result = resultJson({alerts: []});
        try {
            if (mongoInterface.client) {
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
                res.status(Status.SUCCESS).send(result);
                return;
            } else {
                // This is done just for the sake of completion, as it is very
                // unlikely to occur.
                const err = new MongoClientNotInitialised();
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        } catch (err) {
            console.error(err);
            const retrievalErr = new CouldNotRetrieveDataFromMongo();
            res.status(retrievalErr.code).send(errorJson(
                retrievalErr.message));
            return;
        }
    });

app.post('/server/mongo/metrics',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s', req.url);
        const {
            chains,
            systems,
            minTimestamp,
            maxTimestamp,
            noOfMetricsPerSource
        } = req.body;

        // Check that all parameters have been sent
        const missingKeysList: string[] = missingValues({
            chains,
            systems,
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

        const arrayBasedStringParams = {chains, systems};
        for (const [param, value] of Object.entries(arrayBasedStringParams)) {
            if (!Array.isArray(value) ||
                !allElementsInListHaveTypeString(value)) {
                const err = new InvalidParameterValue(
                    `req.body.${param}`);
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        }

        const positiveFloats = {minTimestamp, maxTimestamp};
        for (const [param, value] of Object.entries(positiveFloats)) {
            const parsedFloat = parseFloat(value);
            if (isNaN(parsedFloat) || parsedFloat < 0) {
                const err = new InvalidParameterValue(
                    `req.body.${param}`);
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        }
        const parsedMinTimestamp = parseFloat(minTimestamp);
        const parsedMaxTimestamp = parseFloat(maxTimestamp);

        const parsedNoOfMetricsPerSource = parseInt(noOfMetricsPerSource);
        if (isNaN(parsedNoOfMetricsPerSource) || parsedNoOfMetricsPerSource <=
            0) {
            const err = new InvalidParameterValue(
                'req.body.noOfMetricsPerSource');
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // In the future, we need to retrieve node metrics, hence adding a
        // nodes field. Also, a node ID can be present in both the systems and
        // the nodes fields.

        let result = resultJson({metrics: {}});
        try {
            if (mongoInterface.client) {
                const db = mongoInterface.client.db(mongoDB);
                if (chains.length > 0) {
                    var queryPromise = new Promise<void>((resolve, _) => {
                        systems.forEach(async (source: string,
                                               i: number): Promise<void> => {
                            let queryList: any = [];
                            for (let i = 1; i < chains.length; i++) {
                                queryList.push({$unionWith: chains[i]})
                            }

                            if (!(source in result.result.metrics)) {
                                result.result.metrics[source] = []
                            }

                            const originSource = "$".concat(source);
                            const timestampSource = source.concat(".timestamp");
                            queryList.push(
                                {$match: {doc_type: "system"}},
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
                                result.result.metrics[source] =
                                    result.result.metrics[source].concat(
                                        doc[source])
                            }
                            if (i === systems.length - 1) resolve();
                        });
                    });

                    queryPromise.then(() => {
                        res.status(Status.SUCCESS).send(result);
                        return;
                    });
                } else {
                    res.status(Status.SUCCESS).send(result);
                    return;
                }
            } else {
                // This is done just for the sake of completion, as it is very
                // unlikely to occur.
                const err = new MongoClientNotInitialised();
                res.status(err.code).send(errorJson(err.message));
                return;
            }
        } catch (err) {
            console.error(err);
            const retrievalErr = new CouldNotRetrieveDataFromMongo();
            res.status(retrievalErr.code).send(errorJson(
                retrievalErr.message));
            return;
        }
    });

// ---------------------------------------- Redis Endpoints

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
        if (!isAlertsOverviewInputValid(parentIds)) {
            const err = new InvalidJsonSchema("req.body.parentIds");
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // Construct the redis hashes and keys. The keys are only used to check
        // whether they are available within redis since we get all keys.
        const redisHashes: RedisHashes = getRedisHashes();
        const redisHashesNamespace: RedisKeys = addPrefixToKeys(
            redisHashes, `${uniqueAlerterIdentifier}:`);
        const redisHashesPostfix: RedisKeys = addPostfixToKeys(
            redisHashesNamespace, '_');
        const alertKeysSystem: AlertKeysSystem = getAlertKeysSystem();
        const alertKeysSystemPostfix: RedisKeys = addPostfixToKeys(
            alertKeysSystem, '_');
        const alertKeysNode: AlertKeysNode = getAlertKeysNode();
        const alertKeysNodePostfix: RedisKeys = addPostfixToKeys(
            alertKeysNode, '_');
        const alertKeysGitHubRepo: AlertKeysGitHubRepo =
            getAlertKeysGitHubRepo();
        const alertKeysGitHubRepoPostfix: RedisKeys =
            addPostfixToKeys(alertKeysGitHubRepo, '_');
        const alertKeysDockerHubRepo: AlertKeysDockerHubRepo =
            getAlertKeysDockerHubRepo();
        const alertKeysDockerHubRepoPostfix: RedisKeys =
            addPostfixToKeys(alertKeysDockerHubRepo, '_');

        let alertsData: AlertsOverviewAlertData[] = []
        let result: AlertsOverviewResult = resultJson({});

        if (redisInterface.client) {
            let encounteredError = false;

            // Using multi() means that all commands are only performed once
            // exec() is called, and this is done atomically.
            const redisMulti = redisInterface.client.multi();

            for (const [parentId, sourcesObject] of Object.entries(parentIds)) {
                const parentHash: string =
                    `${redisHashesPostfix.parent}${parentId}`
                result.result[parentId] = {
                    "info": 0,
                    "critical": 0,
                    "warning": 0,
                    "error": 0,
                    "problems": {},
                    "releases": {},
                    "tags": {},
                };

                redisMulti.hgetall(parentHash, (err: Error | null, values: any) => {
                    if (err) {
                        console.error(err);
                        // Skip resolve if an error was already encountered
                        // since call is already resolved.
                        if (!encounteredError) {
                            encounteredError = true;
                            const retrievalErr =
                                new CouldNotRetrieveDataFromRedis(err);
                            res.status(retrievalErr.code).send(errorJson(
                                retrievalErr.message));
                        }
                        return;
                    }

                    if (values === null) {
                        values = {};
                    }

                    // Update info count with keys not found in retrieved keys.
                    sourcesObject.systems.forEach((systemId) => {
                        const constructedKeys: RedisKeys = addPostfixToKeys(
                            alertKeysSystemPostfix, systemId);
                        Object.values(constructedKeys).forEach((key) => {
                            if (!(key in values)) {
                                result.result[parentId].info++;
                            }
                        });
                    });
                    sourcesObject.nodes.forEach((nodeId) => {
                        const constructedKeys: RedisKeys = addPostfixToKeys(
                            alertKeysNodePostfix, nodeId);
                        Object.values(constructedKeys).forEach((key) => {
                            if (!(key in values)) {
                                result.result[parentId].info++;
                            }
                        });
                    });
                    sourcesObject.github_repos.forEach((repoId) => {
                        const constructedKeys: RedisKeys = addPostfixToKeys(
                            alertKeysGitHubRepoPostfix, repoId);
                        Object.values(constructedKeys).forEach((key) => {
                            if (!(key in values)) {
                                result.result[parentId].info++;
                            }
                        });
                    });
                    sourcesObject.dockerhub_repos.forEach((repoId) => {
                        const constructedKeys: RedisKeys = addPostfixToKeys(
                            alertKeysDockerHubRepoPostfix, repoId);
                        Object.values(constructedKeys).forEach((key) => {
                            if (!(key in values)) {
                                result.result[parentId].info++;
                            }
                        });
                    });

                    for (const [key, value] of Object.entries(values)) {
                        // Skip checks if encountered error since
                        // call is already resolved.
                        if (encounteredError) {
                            break;
                        }
                        let found = false;

                        sourcesObject.systems.forEach((systemId) => {
                            if (!found && key.includes(systemId) &&
                                key.includes(alertKeysSystemPrefix)) {
                                found = true;
                                alertsData.push({
                                    parentId: parentId,
                                    monitorableId: systemId,
                                    key: key,
                                    value: value
                                })
                            }
                        });
                        if (!found) {
                            sourcesObject.nodes.forEach((nodeId) => {
                                if (!found && key.includes(nodeId) &&
                                    (key.includes(alertKeysClNodePrefix)
                                        || key.includes(alertKeysEvmNodePrefix)
                                        || (key.includes(
                                            alertKeysCosmosNodePrefix))
                                        || (key.includes(
                                            alertKeysSubstrateNodePrefix))
                                        || (key.includes(
                                            alertKeysClContractPrefix)))
                                ) {
                                    found = true;
                                    alertsData.push({
                                        parentId: parentId,
                                        monitorableId: nodeId,
                                        key: key,
                                        value: value
                                    })
                                }
                            });
                        }
                        if (!found) {
                            sourcesObject.github_repos.forEach((repoId) => {
                                if (!found && key.includes(repoId) &&
                                    key.includes(alertKeysGitHubPrefix)) {
                                    found = true;
                                    alertsData.push({
                                        parentId: parentId,
                                        monitorableId: repoId,
                                        key: key,
                                        value: value
                                    })
                                }
                            });
                        }
                        if (!found) {
                            sourcesObject.dockerhub_repos.forEach((repoId) => {
                                if (!found && key.includes(repoId) &&
                                    key.includes(alertKeysDockerHubPrefix)) {
                                    found = true;
                                    alertsData.push({
                                        parentId: parentId,
                                        monitorableId: repoId,
                                        key: key,
                                        value: value
                                    })
                                }
                            });
                        }

                        if (!found && sourcesObject.include_chain_sourced_alerts) {
                            if (alertKeysChainSourced.includes(key) ||
                                alertKeysChainSourcedWithUniqueIdentifier.some(
                                    alertKey => key.includes(alertKey))) {
                                alertsData.push({
                                    parentId: parentId,
                                    monitorableId: parentId,
                                    key: key,
                                    value: value
                                })
                            }
                        }
                    }
                });
            }

            redisMulti.exec((err: Error | null, _: any) => {
                if (err) {
                    console.error(err);
                    // Skip resolve if an error was already encountered
                    // since call is already resolved.
                    if (!encounteredError) {
                        encounteredError = true;
                        const retrievalErr =
                            new CouldNotRetrieveDataFromRedis(err);
                        res.status(retrievalErr.code).send(errorJson(
                            retrievalErr.message));
                    }
                    return
                }
                // Skip resolve if encountered error since call is already
                // resolved.
                if (!encounteredError) {
                    const currentTimestamp = Math.floor(Date.now() / 1000);
                    alertsData.forEach((data: {
                        parentId: string,
                        monitorableId: string,
                        key: string,
                        value: string
                    }) => {
                        // Skip checks if encountered error since
                        // call is already resolved.
                        if (encounteredError) {
                            return;
                        }
                        let value: any = null;
                        try {
                            value = JSON.parse(data.value);
                        } catch (err) {
                            // This is done just for the sake of
                            // completion, as it is very unlikely
                            // to occur.
                            const invalidValueErr =
                                new InvalidValueRetrievedFromRedis(data.value);
                            res.status(invalidValueErr.code).send(errorJson(
                                invalidValueErr.message));
                            encounteredError = true;
                            return;
                        }
                        if (value && value.constructor === Object &&
                            "message" in value && "severity" in
                            value && "expiry" in value) {
                            // Add array of problems if not
                            // initialised yet and there is indeed
                            // problems.
                            if (value.severity !== Severities.INFO &&
                                !result.result[data.parentId].problems[
                                    data.monitorableId]) {
                                result.result[data.parentId].problems[
                                    data.monitorableId] = []
                            }
                            // If the alerter has detected a new
                            // release add it to the list of
                            // releases
                            const newReleaseKey: string =
                                addPostfixToKeys(alertKeysGitHubRepoPostfix,
                                    data.monitorableId).github_release;
                            if (data.key === newReleaseKey) {
                                result.result[data.parentId].releases[
                                    data.monitorableId] = value
                            }
                            // If the alerter has detected a tag
                            // change, add it to the list of tags
                            const dockerHubTagsKeys =
                                addPostfixToKeys(alertKeysDockerHubRepoPostfix,
                                    data.monitorableId);
                            const changedTagsKeys = [
                                dockerHubTagsKeys.dockerhub_new_tag,
                                dockerHubTagsKeys.dockerhub_updated_tag,
                                dockerHubTagsKeys.dockerhub_deleted_tag
                            ];
                            if (changedTagsKeys.includes(data.key)) {
                                if (!(data.monitorableId in
                                    result.result[data.parentId].tags)) {
                                    result.result[data.parentId].tags[
                                        data.monitorableId] = {
                                        new: {},
                                        updated: {},
                                        deleted: {}
                                    }
                                }
                                switch (data.key) {
                                    case changedTagsKeys[0]:
                                        result.result[data.parentId].tags[
                                            data.monitorableId]
                                            ['new'] = value;
                                        break;
                                    case changedTagsKeys[1]:
                                        result.result[data.parentId].tags[
                                            data.monitorableId]
                                            ['updated'] = value;
                                        break;
                                    case changedTagsKeys[2]:
                                        result.result[data.parentId].tags[
                                            data.monitorableId]
                                            ['deleted'] = value;
                                        break;
                                }
                            }
                            if (value.expiry && currentTimestamp >=
                                value.expiry) {
                                result.result[data.parentId].info++;
                            } else {
                                // Increase the counter and save the
                                // problems.
                                if (value.severity === Severities.INFO) {
                                    result.result[data.parentId].info++;
                                } else if (value.severity ===
                                    Severities.CRITICAL) {
                                    result.result[data.parentId].critical++;
                                    result.result[data.parentId].problems[
                                        data.monitorableId].push(value)
                                } else if (value.severity ===
                                    Severities.WARNING) {
                                    result.result[data.parentId].warning++;
                                    result.result[data.parentId].problems[
                                        data.monitorableId].push(value)
                                } else if (
                                    value.severity === Severities.ERROR) {
                                    result.result[data.parentId].error++;
                                    result.result[data.parentId].problems[
                                        data.monitorableId].push(value)
                                }
                            }
                        } else {
                            // This is done just for the sake of
                            // completion, as it is very unlikely
                            // to occur.
                            const err =
                                new InvalidValueRetrievedFromRedis(
                                    value);
                            res.status(err.code)
                                .send(errorJson(err.message));
                            encounteredError = true;
                            return;
                        }
                    })

                    // Skip resolve if encountered error since call is already
                    // resolved.
                    if (!encounteredError) {
                        res.status(Status.SUCCESS).send(result);
                    }
                }
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
        const parentIds: RedisMetricsInput = req.body.parentIds;

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({parentIds});
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // Check if the passed dict is valid
        if (!isRedisMetricsInputValid(parentIds)) {
            const err = new InvalidJsonSchema("req.body.parentIds");
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // Construct the redis keys inside a JSON object indexed by parent hash
        // and the system/repo id. We also need a way to map the hash to the
        // parent id.
        const parentHashKeys: {
            [key: string]: { [key: string]: string[] }
        } = {};
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
            let encounteredError = false;
            for (const [parentHash, monitorableKeysObject] of Object.entries(
                parentHashKeys)) {
                const parentId: string = parentHashId[parentHash];
                result.result[parentId] = {
                    "system": {},
                    "github": {},
                };
                for (const [monitorableId, keysList] of
                    Object.entries(monitorableKeysObject)) {
                    // Skip checks if encountered error since call
                    // is already resolved.
                    if (encounteredError) {
                        break;
                    }
                    redisMulti.hmget(parentHash, keysList,
                        (err: Error | null, values: any) => {
                            if (err) {
                                console.error(err);
                                // Skip resolve if an error was already
                                // encountered since call is already resolved.
                                if (!encounteredError) {
                                    encounteredError = true;
                                    const retrievalErr =
                                        new CouldNotRetrieveDataFromRedis(err);
                                    res.status(retrievalErr.code).send(
                                        errorJson(retrievalErr.message));
                                }
                                return;
                            }
                            keysList.forEach(
                                (key: string, i: number): void => {
                                    // Skip checks if encountered error since
                                    // call is already resolved.
                                    if (encounteredError) {
                                        return;
                                    }
                                    // Must be stringified JSON.parse does not
                                    // parse `None`
                                    let value: any = null;
                                    try {
                                        value = JSON.parse(JSON.stringify(
                                            values[i]));
                                    } catch (err) {
                                        // This is done just for the sake of
                                        // completion, as it is very unlikely
                                        // to occur.
                                        const invalidValueErr =
                                            new InvalidValueRetrievedFromRedis(
                                                values[i]);
                                        res.status(invalidValueErr.code)
                                            .send(errorJson(
                                                invalidValueErr.message));
                                        encounteredError = true;
                                        return;
                                    }
                                    if (parentIds[parentId].systems.includes(
                                        monitorableId)) {
                                        if (!(monitorableId in
                                            result.result[parentId].system)) {
                                            result.result[parentId]
                                                .system[monitorableId] =
                                                <SystemKeys>{}
                                        }
                                        result.result[parentId]
                                            .system[monitorableId][key.replace(
                                            '_' + monitorableId,
                                            '')] = value;
                                    } else if (parentIds[parentId].repos
                                        .includes(monitorableId)) {
                                        if (!(monitorableId in
                                            result.result[parentId].github)) {
                                            result.result[parentId]
                                                .github[monitorableId] =
                                                <GitHubKeys>{}
                                        }
                                        result.result[parentId]
                                            .github[monitorableId][key.replace(
                                            '_' + monitorableId,
                                            '')] = value;
                                    }

                                    // In the future, we need to retrieve node
                                    // metrics, where a node ID can be present
                                    // in both the systems and the nodes
                                    // fields.
                                });
                        })
                }
            }
            redisMulti.exec((err: Error | null, _: any) => {
                if (err) {
                    console.error(err);
                    // Skip resolve if an error was already encountered
                    // since call is already resolved.
                    if (!encounteredError) {
                        encounteredError = true;
                        const retrievalErr =
                            new CouldNotRetrieveDataFromRedis(err);
                        res.status(retrievalErr.code).send(errorJson(
                            retrievalErr.message));
                    }
                    return
                }
                // Skip resolve if encountered error since call is already
                // resolved.
                if (!encounteredError) {
                    res.status(Status.SUCCESS).send(result);
                }
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

// ---------------------------------------- Ping Endpoints

// ----------------- Common

app.post('/server/common/node-exporter',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const nodeExporterUrl = req.body['url'];

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({
            url: nodeExporterUrl
        });
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        const url = `${nodeExporterUrl}`;

        axios.get(url, {timeout: 3000}).then((response) => {
            if (verifyNodeExporterPing(response.data)) {
                res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
            } else {
                res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            }
        }).catch((err) => {
            if (err.code === 'ECONNABORTED') {
                res.status(Status.TIMEOUT).send(resultJson(PingStatus.TIMEOUT));
            } else {
                console.error(`Axios error: ${err.message}`);
                res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            }
        });
    });

app.post('/server/common/prometheus',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const url = req.body['url'];
        const baseChain = req.body['baseChain'];

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({url, baseChain});
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // At request level
        const agent = new https.Agent({
            rejectUnauthorized: false
        });

        axios.get(url, {timeout: 3000, httpsAgent: agent}).then((response) => {
            if (verifyPrometheusPing(response.data, baseChain)) {
                res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
            } else {
                res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            }
        }).catch((err) => {
            if (err.code === 'ECONNABORTED') {
                res.status(Status.TIMEOUT).send(resultJson(PingStatus.TIMEOUT));
            } else {
                console.error(`Axios error: ${err.message}`);
                res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            }
        });
    });

// ----------------- Cosmos

app.post('/server/cosmos/rest',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const cosmosRestUrl = req.body['url'];

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({
            url: cosmosRestUrl
        });
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        const url = `${cosmosRestUrl}/node_info`;

        axios.get(url, {timeout: 3000}).then((response) => {
            if ('node_info' in response.data) {
                res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
            } else {
                res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            }
        }).catch((err) => {
            if (err.code === 'ECONNABORTED') {
                res.status(Status.TIMEOUT).send(resultJson(PingStatus.TIMEOUT));
            } else {
                console.error(`Axios error: ${err.message}`);
                res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            }
        });
    });

app.post('/server/cosmos/tendermint-rpc',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const tendermintRpcUrl = req.body['url'];

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({
            url: tendermintRpcUrl
        });
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        const url = `${tendermintRpcUrl}/abci_info?`;

        axios.get(url, {timeout: 3000}).then((response) => {
            if ('jsonrpc' in response.data) {
                res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
            } else {
                res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            }
        }).catch((err) => {
            if (err.code === 'ECONNABORTED') {
                res.status(Status.TIMEOUT).send(resultJson(PingStatus.TIMEOUT));
            } else {
                console.error(`Axios error: ${err.message}`);
                res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            }
        });
    });

// ----------------- Substrate

app.post('/server/substrate/websocket',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const substrateWsUrl = req.body['url'];
        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({
            url: substrateWsUrl
        });
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        const substrateIp = process.env.SUBSTRATE_API_IP;
        const substrateApi = process.env.SUBSTRATE_API_PORT;

        if (!substrateIp || !substrateApi) {
            const err = new EnvVariablesNotAvailable('Substrate IP or Substrate API');
            console.error(err.message);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // At request level
        const agent = new https.Agent({
            rejectUnauthorized: false
        });

        const url = `https://${substrateIp}:${substrateApi}/api/rpc/system/syncState?websocket=${substrateWsUrl}`;

        axios.get(url, {timeout: 5000, httpsAgent: agent}).then((_) => {
            res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
        }).catch((err) => {
            if (err.code === 'ECONNABORTED') {
                res.status(Status.TIMEOUT).send(resultJson(PingStatus.TIMEOUT));
            } else {
                console.error(`Axios error: ${err.message}`);
                res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            }
        });
    });

// ----------------- Ethereum

app.post('/server/ethereum/rpc',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const url = req.body['url'];

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({url});
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        try {
            const web3 = new Web3(new Web3.providers.HttpProvider(url));
            const data = await fulfillWithTimeLimit(web3.eth.getBlockNumber(), 3000, -1);

            if (data === -1) {
                res.status(Status.TIMEOUT).send(resultJson(PingStatus.TIMEOUT));
            } else {
                res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
            }
        } catch (err) {
            console.error(`Web3 error: ${err.message}`);
            res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
        }
    });

// ---------------------------------------- Send Test Alert Endpoints

// ----------------- Channels

app.post('/server/channels/opsgenie',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const apiKey = req.body['apiKey'];
        const eu = req.body['eu'];

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({apiKey, eu});
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // If the eu=true set the host to the opsgenie EU url otherwise the sdk will
        // run into an authentication error.
        const host = toBool(String(eu)) ? 'https://api.eu.opsgenie.com' : 'https://api.opsgenie.com';

        // Create OpsGenie client and test alert message
        opsgenie.configure({api_key: apiKey, host});

        // Test alert object
        const alertObject = {
            message: testAlertMessage,
            description: testAlertMessage,
            priority: 'P5',
        };

        // Send test alert
        opsgenie.alertV2.create(alertObject, (err, _) => {
            if (err) {
                console.error(err);
                res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            } else {
                res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
            }
        });
    });

app.post('/server/channels/slack',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const botToken = req.body['botToken'];
        const botChannelId = req.body['botChannelId'];

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({botToken, botChannelId});
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // Create Slack web client and test alert message
        const client = new WebClient(botToken);

        // Test alert object
        const alertObject = {
            text: testAlertMessage,
            channel: botChannelId
        };

        // Send test alert
        try {
            await client.chat.postMessage(alertObject);
        } catch (err) {
            console.error(err);
            res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            return;
        }

        res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
    });

app.post('/server/channels/telegram',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const botToken = req.body['botToken'];
        const botChatId = req.body['botChatId'];

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({botToken, botChatId});
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
        const params = {
            chat_id: botChatId,
            text: testAlertMessage,
            parse_mode: 'Markdown'
        }

        axios.get(url, {timeout: 3000, params}).then(() => {
            res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
        }).catch((err) => {
            console.error(err);
            if (err.code === 'ECONNABORTED') {
                res.status(Status.TIMEOUT).send(resultJson(PingStatus.TIMEOUT));
            } else {
                res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            }
        });
    });

app.post('/server/channels/pagerduty',
    async (req, res) => {
    console.log('Received POST request for %s', req.url);
    const integrationKey = req.body['integrationKey'];

    // Check if some required keys are missing in the body object, if yes
    // notify the client.
    const missingKeysList: string[] = missingValues({integrationKey});
    if (missingKeysList.length !== 0) {
        const err = new MissingKeysInBody(...missingKeysList);
        res.status(err.code).send(errorJson(err.message));
        return;
    }

    // Send test alert event
    event({
        data: {
            routing_key: integrationKey,
            event_action: 'trigger',
            payload: {
                summary: testAlertMessage,
                source: 'PANIC',
                severity: 'info',
            },
        }
    }).then(() => {
        res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
    }).catch((err) => {
        console.error(err);
        res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
    });
});

app.post('/server/channels/twilio',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const accountSid = req.body['accountSid'];
        const authToken = req.body['authToken'];
        const twilioPhoneNumber = req.body['twilioPhoneNumber'];
        const phoneNumberToDial = req.body['phoneNumberToDial'];

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({
            accountSid, authToken, twilioPhoneNumber, phoneNumberToDial
        });
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        let client;

        try {
            client = twilio(accountSid, authToken);
        } catch (err) {
            console.error(err);
            res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
            return;
        }

        client.calls.create({
            twiml: '<Response><Reject/></Response>',
            to: phoneNumberToDial,
            from: twilioPhoneNumber
        }).then(() => {
            res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
        }).catch((err) => {
            console.error(err);
            res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
        });
    });

app.post('/server/channels/email',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s %s', req.url, req.body);
        const smtp = req.body['smtp'];
        const port = req.body['port'];
        const from = req.body['from'];
        const to = req.body['to'];
        const username = req.body['username'];
        const password = req.body['password'];

        // Check if some required keys are missing in the body object, if yes
        // notify the client.
        const missingKeysList: string[] = missingValues({
            smtp, port, from, to, username, password
        });
        if (missingKeysList.length !== 0) {
            const err = new MissingKeysInBody(...missingKeysList);
            res.status(err.code).send(errorJson(err.message));
            return;
        }

        // Create mail transport (essentially an email client)
        const transport = nodemailer.createTransport({
            host: smtp,
            port,
            auth: username && password ?
                {
                    user: username,
                    pass: password
                } : undefined,
        });

        // If transporter valid, create and send test email
        transport.verify((verifyTransportErr, _) => {
            if (verifyTransportErr) {
                console.error(verifyTransportErr);
                res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
                return;
            }

            const message = {
                from,
                to,
                subject: testAlertMessage,
                text: testAlertMessage,
            };

            // Send test email
            transport.sendMail(message, (sendMailErr, _) => {
                if (sendMailErr) {
                    console.error(sendMailErr);
                    res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
                    return;
                }
                res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
            });
        });
    });

// ----------------- Repositories

app.post('/server/repositories/github',
  async (req: express.Request, res: express.Response) => {
      console.log('Received POST request for %s %s', req.url, req.body);
      const repoName = req.body['name'];

      // Check if some required keys are missing in the body object, if yes
      // notify the client.
      const missingKeysList: string[] = missingValues({
          repoName
      });
      if (missingKeysList.length !== 0) {
          const err = new MissingKeysInBody(...missingKeysList);
          res.status(err.code).send(errorJson(err.message));
          return;
      }

      const url = `https://api.github.com/repos/${repoName}`;

      axios.get(url, {timeout: 3000}).then((response) => {
          if(response.status === 200){
              res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
          } else {
              res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
          }
      }).catch((err) => {
          if (err.code === 'ECONNABORTED') {
              res.status(Status.TIMEOUT).send(resultJson(PingStatus.TIMEOUT));
          } else {
              console.error(`Axios error: ${err.message}`);
              res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
          }
      });
  });

app.post('/server/repositories/dockerhub',
  async (req: express.Request, res: express.Response) => {
      console.log('Received POST request for %s %s', req.url, req.body);
      const repoName = req.body['name'];

      // Check if some required keys are missing in the body object, if yes
      // notify the client.
      const missingKeysList: string[] = missingValues({
          repoName
      });
      if (missingKeysList.length !== 0) {
          const err = new MissingKeysInBody(...missingKeysList);
          res.status(err.code).send(errorJson(err.message));
          return;
      }

      const url = `https://registry.hub.docker.com/v2/repositories/${repoName}`;

      axios.get(url, {timeout: 3000}).then((response) => {
          if('name' in response.data && 'user' in response.data){
              res.status(Status.SUCCESS).send(resultJson(PingStatus.SUCCESS));
          } else {
              res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
          }
      }).catch((err) => {
          if (err.code === 'ECONNABORTED') {
              res.status(Status.TIMEOUT).send(resultJson(PingStatus.TIMEOUT));
          } else {
              console.error(`Axios error: ${err.message}`);
              res.status(Status.ERROR).send(resultJson(PingStatus.ERROR));
          }
      });
  });




// ---------------------------------------- Server defaults

app.get('/server/*', async (req: express.Request,
                            res: express.Response) => {
    console.log('Received GET request for %s', req.url);
    const err: InvalidEndpoint = new InvalidEndpoint(req.url);
    res.status(err.code).send(errorJson(err.message));
});

app.post('/server/*', async (req: express.Request,
                             res: express.Response) => {
    console.log('Received POST request for %s', req.url);
    const err = new InvalidEndpoint(req.url);
    res.status(err.code).send(errorJson(err.message));
});

// ---------------------------------------- Server redirects

app.get('/*', async (req: express.Request, res: express.Response) => {
    res.redirect('/api-docs')
});

app.post('/*', async (req: express.Request,
                      res: express.Response) => {
    res.redirect('/api-docs')
});

// ---------------------------------------- Start listen

const port = parseInt(process.env.API_PORT || "9001");
// Create Https server
const server = https.createServer(httpsOptions, app);

server.once('error', function (err: any) {
    if (err.code === 'EADDRINUSE') {
        console.error('port is currently in use');
    }
});

// Listen for requests
server.listen(port, () => console.log('Listening on %s', port));

//TODO: Need to add authentication, even to the respective middleware functions

export {app, server, redisInterval, mongoInterval};
