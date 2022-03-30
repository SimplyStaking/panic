import MongoClient from "mongodb";
import {MongoClientNotInitialised} from "./errors";
import {
    MSG_MONGO_CONNECTION_ESTABLISHED,
    MSG_MONGO_COULD_NOT_DISCONNECT,
    MSG_MONGO_COULD_NOT_ESTABLISH_CONNECTION,
    MSG_MONGO_DISCONNECTED
} from "./msgs";

export const MonitorablesCollection = 'monitorables';

export class MongoInterface {
    private readonly url: string;
    private readonly options: MongoClient.MongoClientOptions;
    private _client?: MongoClient.MongoClient;

    constructor(options: MongoClient.MongoClientOptions,
                host: string = "localhost", port: number = 27017) {
        this.options = options;
        this.url = `mongodb://${host}:${port}`;
        this._client = undefined;
    }

    get client() {
        return this._client
    }

    async connect() {
        if (this._client && this._client.isConnected()) {
            return;
        }
        try {
            this._client = await MongoClient.connect(this.url, this.options);
            console.log(MSG_MONGO_CONNECTION_ESTABLISHED)
        } catch (err) {
            console.error(MSG_MONGO_COULD_NOT_ESTABLISH_CONNECTION);
            console.error(err);
        }
    }

    async disconnect() {
        if (this._client) {
            try {
                if (this._client.isConnected()) {
                    await this._client.close();
                    console.log(MSG_MONGO_DISCONNECTED)
                }
            } catch (err) {
                console.error(MSG_MONGO_COULD_NOT_DISCONNECT);
                console.error(err)
            }
        } else {
            throw new MongoClientNotInitialised()
        }
    }
}
