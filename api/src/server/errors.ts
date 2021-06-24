// Errors that may be raised by the server

import {baseChainsRedis} from "./redis";

export enum UIServerErrorCode {
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
    E_542 = 542,
    E_543 = 543,
    E_544 = 544,
    E_545 = 545,
    E_546 = 546,
    E_547 = 547,
    E_548 = 548,
    E_549 = 549,
    E_550 = 550,
    E_551 = 551,
}

class UIServerError extends Error {
    code: UIServerErrorCode;

    constructor(message: string, code: UIServerErrorCode) {
        super(message);
        this.code = code;
    }
}

export class MissingFile extends UIServerError {
    constructor(filePath: string) {
        let message: string = `Cannot find ${filePath}.`;
        let code: UIServerErrorCode = UIServerErrorCode.E_530;
        super(message, code)
    }
}

export class InvalidEndpoint extends UIServerError {
    constructor(endpoint: string) {
        let message: string = `'${endpoint}' is an invalid endpoint.`;
        let code: UIServerErrorCode = UIServerErrorCode.E_531;
        super(message, code)
    }
}

export class MissingKeysInBody extends UIServerError {
    constructor(...keys: string[]) {
        let message: string = `Missing key(s) ${keys.join(', ')} in body`;
        let code: UIServerErrorCode = UIServerErrorCode.E_532;
        super(message, code)
    }
}

// Redis related errors
export class RedisClientNotInitialised extends UIServerError {
    constructor() {
        let message: string = 'Redis client not initialised.';
        let code: UIServerErrorCode = UIServerErrorCode.E_533;
        super(message, code)
    }
}

export class CouldNotRetrieveDataFromRedis extends UIServerError {
    constructor() {
        let message: string = 'Could not retrieve data from Redis.';
        let code: UIServerErrorCode = UIServerErrorCode.E_534;
        super(message, code)
    }
}

// Mongo related errors
export class MongoClientNotInitialised extends UIServerError {
    constructor() {
        let message: string = 'Mongo client not initialised.';
        let code: UIServerErrorCode = UIServerErrorCode.E_535;
        super(message, code)
    }

}

export class CouldNotRetrieveDataFromMongo extends UIServerError {
    constructor() {
        let message: string = 'Could not retrieve data from Mongo.';
        let code: UIServerErrorCode = UIServerErrorCode.E_536;
        super(message, code)
    }
}

// Other Errors
export class InvalidBaseChains extends UIServerError {
    constructor(...baseChains: any[]) {
        let message: string = `Invalid base chain(s) ${baseChains}.
        Please enter a list containing some of these values: ${baseChainsRedis.join(', ')}`;

        let code: UIServerErrorCode = UIServerErrorCode.E_537;
        super(message, code)
    }
}

export class InvalidJsonSchema extends UIServerError {
    constructor(whichJson: string) {
        let message: string = `${whichJson} does not obey the required schema`;
        let code: UIServerErrorCode = UIServerErrorCode.E_538;
        super(message, code)
    }
}

export class InvalidParameterValue extends UIServerError {
    constructor(parameter: string) {
        let message: string = `An invalid value was given to ${parameter}`;
        let code: UIServerErrorCode = UIServerErrorCode.E_539;
        super(message, code)
    }
}
