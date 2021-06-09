"use strict";
// Errors that may be raised by the server
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        if (typeof b !== "function" && b !== null)
            throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.InvalidParameterValue = exports.InvalidJsonSchema = exports.InvalidBaseChains = exports.CouldNotRetrieveDataFromMongo = exports.MongoClientNotInitialised = exports.CouldNotRetrieveDataFromRedis = exports.RedisClientNotInitialised = exports.MissingKeysInBody = exports.InvalidEndpoint = exports.MissingFile = exports.UIServerErrorCode = void 0;
var redis_1 = require("./redis");
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
var UIServerError = /** @class */ (function (_super) {
    __extends(UIServerError, _super);
    function UIServerError(message, code) {
        var _this = _super.call(this, message) || this;
        _this.code = code;
        return _this;
    }
    return UIServerError;
}(Error));
var MissingFile = /** @class */ (function (_super) {
    __extends(MissingFile, _super);
    function MissingFile(filePath) {
        var _this = this;
        var message = "Cannot find " + filePath + ".";
        var code = UIServerErrorCode.E_530;
        _this = _super.call(this, message, code) || this;
        return _this;
    }
    return MissingFile;
}(UIServerError));
exports.MissingFile = MissingFile;
var InvalidEndpoint = /** @class */ (function (_super) {
    __extends(InvalidEndpoint, _super);
    function InvalidEndpoint(endpoint) {
        var _this = this;
        var message = "'" + endpoint + "' is an invalid endpoint.";
        var code = UIServerErrorCode.E_531;
        _this = _super.call(this, message, code) || this;
        return _this;
    }
    return InvalidEndpoint;
}(UIServerError));
exports.InvalidEndpoint = InvalidEndpoint;
var MissingKeysInBody = /** @class */ (function (_super) {
    __extends(MissingKeysInBody, _super);
    function MissingKeysInBody() {
        var keys = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            keys[_i] = arguments[_i];
        }
        var _this = this;
        var message = "Missing key(s) " + keys.join(', ') + " in body";
        var code = UIServerErrorCode.E_532;
        _this = _super.call(this, message, code) || this;
        return _this;
    }
    return MissingKeysInBody;
}(UIServerError));
exports.MissingKeysInBody = MissingKeysInBody;
// Redis related errors
var RedisClientNotInitialised = /** @class */ (function (_super) {
    __extends(RedisClientNotInitialised, _super);
    function RedisClientNotInitialised() {
        var _this = this;
        var message = "Redis client not initialised.";
        var code = UIServerErrorCode.E_533;
        _this = _super.call(this, message, code) || this;
        return _this;
    }
    return RedisClientNotInitialised;
}(UIServerError));
exports.RedisClientNotInitialised = RedisClientNotInitialised;
var CouldNotRetrieveDataFromRedis = /** @class */ (function (_super) {
    __extends(CouldNotRetrieveDataFromRedis, _super);
    function CouldNotRetrieveDataFromRedis() {
        var _this = this;
        var message = "Could not retrieve data from Redis.";
        var code = UIServerErrorCode.E_534;
        _this = _super.call(this, message, code) || this;
        return _this;
    }
    return CouldNotRetrieveDataFromRedis;
}(UIServerError));
exports.CouldNotRetrieveDataFromRedis = CouldNotRetrieveDataFromRedis;
// Mongo related errors
var MongoClientNotInitialised = /** @class */ (function (_super) {
    __extends(MongoClientNotInitialised, _super);
    function MongoClientNotInitialised() {
        var _this = this;
        var message = "Mongo client not initialised.";
        var code = UIServerErrorCode.E_535;
        _this = _super.call(this, message, code) || this;
        return _this;
    }
    return MongoClientNotInitialised;
}(UIServerError));
exports.MongoClientNotInitialised = MongoClientNotInitialised;
var CouldNotRetrieveDataFromMongo = /** @class */ (function (_super) {
    __extends(CouldNotRetrieveDataFromMongo, _super);
    function CouldNotRetrieveDataFromMongo() {
        var _this = this;
        var message = "Could not retrieve data from Mongo.";
        var code = UIServerErrorCode.E_536;
        _this = _super.call(this, message, code) || this;
        return _this;
    }
    return CouldNotRetrieveDataFromMongo;
}(UIServerError));
exports.CouldNotRetrieveDataFromMongo = CouldNotRetrieveDataFromMongo;
// Other Errors
var InvalidBaseChains = /** @class */ (function (_super) {
    __extends(InvalidBaseChains, _super);
    function InvalidBaseChains() {
        var baseChains = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            baseChains[_i] = arguments[_i];
        }
        var _this = this;
        var message = "Invalid base chain(s) " + baseChains + ". Please " +
            'enter a list containing some of these values: ' +
            ("" + redis_1.baseChainsRedis.join(', '));
        var code = UIServerErrorCode.E_537;
        _this = _super.call(this, message, code) || this;
        return _this;
    }
    return InvalidBaseChains;
}(UIServerError));
exports.InvalidBaseChains = InvalidBaseChains;
var InvalidJsonSchema = /** @class */ (function (_super) {
    __extends(InvalidJsonSchema, _super);
    function InvalidJsonSchema(whichJson) {
        var _this = this;
        var message = whichJson + " does not obey the required schema";
        var code = UIServerErrorCode.E_538;
        _this = _super.call(this, message, code) || this;
        return _this;
    }
    return InvalidJsonSchema;
}(UIServerError));
exports.InvalidJsonSchema = InvalidJsonSchema;
var InvalidParameterValue = /** @class */ (function (_super) {
    __extends(InvalidParameterValue, _super);
    function InvalidParameterValue(parameter) {
        var _this = this;
        var message = "An invalid value was given to " + parameter;
        var code = UIServerErrorCode.E_539;
        _this = _super.call(this, message, code) || this;
        return _this;
    }
    return InvalidParameterValue;
}(UIServerError));
exports.InvalidParameterValue = InvalidParameterValue;
