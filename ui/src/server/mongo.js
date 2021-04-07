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
exports.MongoInterface = void 0;
const mongodb_1 = __importDefault(require("mongodb"));
const errors_1 = require("./errors");
const msgs_1 = require("./msgs");
class MongoInterface {
    constructor(options, host = "localhost", port = 27017) {
        this.options = options;
        this.url = `mongodb://${host}:${port}`;
        this._client = undefined;
    }
    get client() {
        return this._client;
    }
    connect() {
        return __awaiter(this, void 0, void 0, function* () {
            if (this._client && this._client.isConnected()) {
                return;
            }
            try {
                this._client = yield mongodb_1.default.connect(this.url, this.options);
                console.log(msgs_1.MSG_MONGO_CONNECTION_ESTABLISHED);
            }
            catch (err) {
                console.error(msgs_1.MSG_MONGO_COULD_NOT_ESTABLISH_CONNECTION);
                console.error(err);
            }
        });
    }
    disconnect() {
        return __awaiter(this, void 0, void 0, function* () {
            if (this._client) {
                try {
                    if (this._client.isConnected()) {
                        yield this._client.close();
                        console.log(msgs_1.MSG_MONGO_DISCONNECTED);
                    }
                }
                catch (err) {
                    console.error(msgs_1.MSG_MONGO_COULD_NOT_DISCONNECT);
                    console.error(err);
                }
            }
            else {
                throw new errors_1.MongoClientNotInitialised();
            }
        });
    }
}
exports.MongoInterface = MongoInterface;
