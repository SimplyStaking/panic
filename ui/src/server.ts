import {readFile} from "./server/files";
import path from "path"
import {HttpsOptions} from "./server/types";
import {InvalidEndpoint} from './server/errors'
import {errorJson} from "./server/utils";
import express from "express";
import bodyParser from "body-parser";
import cookieParser from "cookie-parser";

// Import certificate files
const httpsKey: Buffer = readFile(path.join(__dirname, '../../', 'certificates',
    'key.pem'));
const httpsCert: Buffer = readFile(path.join(__dirname, '../../', 'certificates',
    'cert.pem'));
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

// // ---------------------------------------- Start listen
//
// const port = process.env.INSTALLER_PORT || 8000;
//
// (async () => {
//     try {
//         // Check that installer credentials are in the .env. If not inform the user
//         // and terminate the server.
//         checkInstAuthCredentials();
//         // Load authentication details before listening for requests to avoid
//         // unexpected behaviour.
//         await loadAuthenticationToDB();
//     } catch (err) {
//         console.log(err);
//         process.exit(0);
//     }
//     // Create Https server
//     const server = https.createServer(httpsOptions, app);
//     // Listen for requests
//     server.listen(port, () => console.log('Listening on %s', port));
// })().catch((err) => console.log(err));

// TODO: Need to add authentication, even to the respective middleware functions
// TODO: Test multiple invalid routes such as /server/* .. bad route etc
