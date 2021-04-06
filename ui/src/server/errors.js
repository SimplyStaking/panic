"use strict";
// Errors that may be raised by the server
Object.defineProperty(exports, "__esModule", { value: true });
exports.InvalidJsonSchema = exports.InvalidBaseChains = exports.CouldNotRetrieveDataFromRedis = exports.RedisClientNotInitialised = exports.MissingKeysInBody = exports.InvalidEndpoint = exports.MissingFile = exports.UIServerErrorCode = void 0;
const redis_1 = require("./redis");
var UIServerErrorCode;
(function (UIServerErrorCode) {
    UIServerErrorCode[UIServerErrorCode["E_530"] = 530] = "E_530";
    UIServerErrorCode[UIServerErrorCode["E_531"] = 531] = "E_531";
    UIServerErrorCode[UIServerErrorCode["E_532"] = 532] = "E_532";
    UIServerErrorCode[UIServerErrorCode["E_533"] = 533] = "E_533";
    UIServerErrorCode[UIServerErrorCode["E_534"] = 534] = "E_534";
    UIServerErrorCode[UIServerErrorCode["E_535"] = 535] = "E_535";
    UIServerErrorCode[UIServerErrorCode["E_536"] = 536] = "E_536";
    UIServerErrorCode[UIServerErrorCode["E_537"] = 537] = "E_537";
    UIServerErrorCode[UIServerErrorCode["E_538"] = 538] = "E_538";
    UIServerErrorCode[UIServerErrorCode["E_539"] = 539] = "E_539";
    UIServerErrorCode[UIServerErrorCode["E_540"] = 540] = "E_540";
    UIServerErrorCode[UIServerErrorCode["E_541"] = 541] = "E_541";
    UIServerErrorCode[UIServerErrorCode["E_542"] = 542] = "E_542";
    UIServerErrorCode[UIServerErrorCode["E_543"] = 543] = "E_543";
    UIServerErrorCode[UIServerErrorCode["E_544"] = 544] = "E_544";
    UIServerErrorCode[UIServerErrorCode["E_545"] = 545] = "E_545";
    UIServerErrorCode[UIServerErrorCode["E_546"] = 546] = "E_546";
    UIServerErrorCode[UIServerErrorCode["E_547"] = 547] = "E_547";
    UIServerErrorCode[UIServerErrorCode["E_548"] = 548] = "E_548";
    UIServerErrorCode[UIServerErrorCode["E_549"] = 549] = "E_549";
    UIServerErrorCode[UIServerErrorCode["E_550"] = 550] = "E_550";
    UIServerErrorCode[UIServerErrorCode["E_551"] = 551] = "E_551";
})(UIServerErrorCode = exports.UIServerErrorCode || (exports.UIServerErrorCode = {}));
class UIServerError extends Error {
    constructor(message, code) {
        super(message);
        this.code = code;
    }
}
class MissingFile extends UIServerError {
    constructor(filePath) {
        let message = `Cannot find ${filePath}.`;
        let code = UIServerErrorCode.E_530;
        super(message, code);
    }
}
exports.MissingFile = MissingFile;
class InvalidEndpoint extends UIServerError {
    constructor(endpoint) {
        let message = `'${endpoint}' is an invalid endpoint.`;
        let code = UIServerErrorCode.E_531;
        super(message, code);
    }
}
exports.InvalidEndpoint = InvalidEndpoint;
class MissingKeysInBody extends UIServerError {
    constructor(...keys) {
        let message = `Missing key(s) ${keys.join(', ')} in body`;
        let code = UIServerErrorCode.E_532;
        super(message, code);
    }
}
exports.MissingKeysInBody = MissingKeysInBody;
// Redis related errors
class RedisClientNotInitialised extends UIServerError {
    constructor() {
        let message = `Redis client not initialised.`;
        let code = UIServerErrorCode.E_533;
        super(message, code);
    }
}
exports.RedisClientNotInitialised = RedisClientNotInitialised;
class CouldNotRetrieveDataFromRedis extends UIServerError {
    constructor() {
        let message = "Could not retrieve data from Redis.";
        let code = UIServerErrorCode.E_534;
        super(message, code);
    }
}
exports.CouldNotRetrieveDataFromRedis = CouldNotRetrieveDataFromRedis;
// Other Errors
class InvalidBaseChains extends UIServerError {
    constructor(...baseChains) {
        let message = `Invalid base chain(s) ${baseChains}. Please ` +
            'enter a list containing some of these values: ' +
            `${redis_1.baseChainsRedis.join(', ')}`;
        let code = UIServerErrorCode.E_535;
        super(message, code);
    }
}
exports.InvalidBaseChains = InvalidBaseChains;
class InvalidJsonSchema extends UIServerError {
    constructor(whichJson) {
        let message = `${whichJson} does not obey the required schema`;
        let code = UIServerErrorCode.E_536;
        super(message, code);
    }
}
exports.InvalidJsonSchema = InvalidJsonSchema;
