import {readFile} from "./server/files";
import path from "path"
import https from "https"
import {
    BaseChainKeys,
    HttpsOptions,
    monitorablesInfoResult,
    RedisKeys
} from "./server/types";
import {
    CouldNotRetrieveDataFromRedis,
    InvalidBaseChains,
    InvalidEndpoint,
    MissingParameters,
    RedisClientNotInitialised
} from './server/errors'
import {
    allElementsInList,
    errorJson,
    getElementsNotInList,
    missingValues,
    resultJson,
    SUCCESS_STATUS
} from "./server/utils";
import express from "express";
import bodyParser from "body-parser";
import cookieParser from "cookie-parser";
import {
    addPostfixToKeys,
    baseChainsRedis,
    getBaseChainKeys,
    RedisInterface
} from "./server/redis"

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
        return res.sendStatus(400); // Bad request
    }

    next();
});

// Connect with Redis
const redisHost = process.env.REDIS_IP;
const redisPort = parseInt(process.env.REDIS_PORT || "6379");
const redisDB = parseInt(process.env.REDIS_DB || "10");
const redisInterface = new RedisInterface(redisHost, redisPort, redisDB);
redisInterface.connect();

// Check the redis connection every 3 seconds. If the connection was dropped,
// re-connect.
setInterval(() => {
    redisInterface.connect();
}, 3000);

// ---------------------------------------- Redis Endpoints

// This endpoint expects requests with at least one base chain (Cosmos,
// Substrate, or General) in a list inside the json body structure.
app.post('/server/redis/monitorablesInfo',
    async (req: express.Request, res: express.Response) => {
        console.log('Received POST request for %s', req.url);
        const {baseChains} = req.body;

        // Check if some required parameters are missing, if yes notify the
        // client.
        const missingParamsList: string[] = missingValues({baseChains});
        if (missingParamsList.length !== 0) {
            const err = new MissingParameters(...missingParamsList);
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
        const baseChainKeysPostfix: RedisKeys = addPostfixToKeys(
            baseChainKeys, '_');
        const constructedKeys: string[] = baseChains.map(
            (baseChain: string): string => {
                return baseChainKeysPostfix.monitorables_info + baseChain
            });

        let result: monitorablesInfoResult = resultJson({});
        if (redisInterface.client) {
            redisInterface.client.mget(constructedKeys, (err, values) => {
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

const port: number = parseInt(process.env.UI_DASHBOARD_PORT || "9000");

(async () => {
    // Create Https server
    const server = https.createServer(httpsOptions, app);
    // Listen for requests
    server.listen(port, () => console.log('Listening on %s', port));
})().catch((err) => console.log(err));

// TODO: Need to add authentication, even to the respective middleware functions
