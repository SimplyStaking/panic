// Errors that may be raised by the server

import {baseChains} from "./constants";

export enum ServerErrorCode {
    E_530 = 530,
    E_531 = 531,
    E_532 = 532,
    E_533 = 533,
    E_534 = 534,
    E_535 = 535,
    E_536 = 536,
    E_537 = 537,
    E_538 = 538,
    E_539 = 539,
    E_540 = 540,
    E_541 = 541,
}

class ServerError extends Error {
    code: ServerErrorCode;

    constructor(message: string, code: ServerErrorCode) {
        super(message);
        this.code = code;
    }
}

export class MissingFile extends ServerError {
    constructor(filePath: string) {
        let message: string = `Error: Cannot find ${filePath}.`;
        let code: ServerErrorCode = ServerErrorCode.E_530;
        super(message, code);
    }
}

export class InvalidEndpoint extends ServerError {
    constructor(endpoint: string) {
        let message: string = `Error: '${endpoint}' is an invalid endpoint.`;
        let code: ServerErrorCode = ServerErrorCode.E_531;
        super(message, code);
    }
}

export class MissingKeysInBody extends ServerError {
    constructor(...keys: string[]) {
        let message: string = `Error: Missing key(s) ${keys.join(
            ', ')} in body.`;
        let code: ServerErrorCode = ServerErrorCode.E_532;
        super(message, code);
    }
}

// Redis related errors
export class RedisClientNotInitialised extends ServerError {
    constructor() {
        let message: string = 'Error: Redis client not initialised.';
        let code: ServerErrorCode = ServerErrorCode.E_533;
        super(message, code);
    }
}

export class CouldNotRetrieveDataFromRedis extends ServerError {
    constructor(error: Error) {
        let message: string = 'Error: ' + error.name + ' retrieved from Redis: '
            + error.message + '.';
        let code: ServerErrorCode = ServerErrorCode.E_534;
        super(message, code);
    }
}

// Mongo related errors
export class MongoClientNotInitialised extends ServerError {
    constructor() {
        let message: string = 'Error: Mongo client not initialised.';
        let code: ServerErrorCode = ServerErrorCode.E_535;
        super(message, code);
    }

}

export class CouldNotRetrieveDataFromMongo extends ServerError {
    constructor() {
        let message: string = 'Error: Could not retrieve data from Mongo.';
        let code: ServerErrorCode = ServerErrorCode.E_536;
        super(message, code);
    }
}

// Other Errors
export class InvalidBaseChains extends ServerError {
    constructor(...baseChainsInput: any[]) {
        let message: string = 'Error: Invalid base chain(s) ' +
            baseChainsInput.join(', ') +
            '. Please enter a list containing some of these values: ' +
            baseChains.join(', ') + '.'

        let code: ServerErrorCode = ServerErrorCode.E_537;
        super(message, code);
    }
}

export class InvalidJsonSchema extends ServerError {
    constructor(whichJson: string) {
        let message: string = 'Error: ' + whichJson +
            ' does not obey the required schema.';
        let code: ServerErrorCode = ServerErrorCode.E_538;
        super(message, code);
    }
}

export class InvalidParameterValue extends ServerError {
    constructor(parameter: string) {
        let message: string = 'Error: An invalid value was given to ' +
            parameter + '.';
        let code: ServerErrorCode = ServerErrorCode.E_539;
        super(message, code);
    }
}

export class InvalidValueRetrievedFromRedis extends ServerError {
    constructor(value: any) {
        let message: string = 'Error: Invalid value retrieved from Redis: ' +
            value + '.';
        let code: ServerErrorCode = ServerErrorCode.E_540;
        super(message, code);
    }
}
