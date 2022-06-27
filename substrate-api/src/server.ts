import * as dotenv from "dotenv";
import path from "path";
import https from "https";
import express from "express";
import {InvalidEndpoint} from "./errors/server";
import {errorJson} from "./utils/response";
import {readFile} from "./utils/file";
import {HttpsOptions} from "./types/server";
import {BAD_REQ_STATUS} from "./utils/constants";
import {WsInterfacesManager} from "./utils/api_interface";
import {queryInterface} from "./routes/query";
import {rpcInterface} from "./routes/rpc";
import {deriveInterface} from "./routes/derive";
import {customInterface} from "./routes/custom";

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
app.use((err: any, req: express.Request, res: express.Response,
         next: express.NextFunction) => {
    // This check makes sure this is a JSON parsing issue
    if (err instanceof SyntaxError && 'body' in err) {
        console.error(err);
        return res.sendStatus(BAD_REQ_STATUS); // Bad request
    }

    next();
});

// Websocket connections manager
let wsInterfaces = new WsInterfacesManager();

// ---------------------------------------- Query endpoints

queryInterface(app, wsInterfaces);

// ---------------------------------------- RPC endpoints

rpcInterface(app, wsInterfaces);

// ---------------------------------------- Derive endpoints

deriveInterface(app, wsInterfaces);

// ---------------------------------------- Custom endpoints

customInterface(app, wsInterfaces);

// ---------------------------------------- Server defaults

app.get('/*', async (req: express.Request, res: express.Response) => {
    console.log('Received GET request for %s', req.url);
    const err: InvalidEndpoint = new InvalidEndpoint(req.url);
    return res.status(BAD_REQ_STATUS).send(errorJson(
        {
            'message': err.message,
            'code': err.code
        }
    ));
});

app.post('/*', async (req: express.Request, res: express.Response) => {
    console.log('Received POST request for %s', req.url);
    const err = new InvalidEndpoint(req.url);
    return res.status(BAD_REQ_STATUS).send(errorJson(
        {
            'message': err.message,
            'code': err.code
        }
    ));
});

// ---------------------------------------- Start listen

const port = parseInt(process.env.SUBSTRATE_API_PORT || "8080");

// Create Https server
const server = https.createServer(httpsOptions, app);

// Listen for requests
server.listen(port, () => console.log('Listening on %s', port));

export {app, server};
