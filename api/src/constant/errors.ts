// Errors that may be raised by the server
import {baseChains, Status} from "./server";

class ServerError extends Error {
    code: Status;

    constructor(message: string, code: Status) {
        super(message);
        this.code = code;
    }
}

export class MissingFile extends ServerError {
    constructor(filePath: string) {
        let message: string = `Error: Cannot find ${filePath}.`;
        let code: Status = Status.E_530;
        super(message, code);
    }
}

export class InvalidEndpoint extends ServerError {
    constructor(endpoint: string) {
        let message: string = `Error: '${endpoint}' is an invalid endpoint.`;
        let code: Status = Status.E_531;
        super(message, code);
    }
}

export class MissingKeysInBody extends ServerError {
    constructor(...keys: string[]) {
        let message: string = `Error: Missing key(s) ${keys.join(
            ', ')} in body.`;
        let code: Status = Status.E_532;
        super(message, code);
    }
}

// Redis related errors
export class RedisClientNotInitialised extends ServerError {
    constructor() {
        let message: string = 'Error: Redis client not initialised.';
        let code: Status = Status.E_533;
        super(message, code);
    }
}

export class CouldNotRetrieveDataFromRedis extends ServerError {
    constructor(error: Error) {
        let message: string = 'Error: ' + error.name + ' retrieved from Redis: '
            + error.message + '.';
        let code: Status = Status.E_534;
        super(message, code);
    }
}

// Mongo related errors
export class MongoClientNotInitialised extends ServerError {
    constructor() {
        let message: string = 'Error: Mongo client not initialised.';
        let code: Status = Status.E_535;
        super(message, code);
    }

}

export class CouldNotRetrieveDataFromMongo extends ServerError {
    constructor() {
        let message: string = 'Error: Could not retrieve data from Mongo.';
        let code: Status = Status.E_536;
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

        let code: Status = Status.E_537;
        super(message, code);
    }
}

export class InvalidJsonSchema extends ServerError {
    constructor(whichJson: string) {
        let message: string = 'Error: ' + whichJson +
            ' does not obey the required schema.';
        let code: Status = Status.E_538;
        super(message, code);
    }
}

export class InvalidParameterValue extends ServerError {
    constructor(parameter: string) {
        let message: string = 'Error: An invalid value was given to ' +
            parameter + '.';
        let code: Status = Status.E_539;
        super(message, code);
    }
}

export class InvalidValueRetrievedFromRedis extends ServerError {
    constructor(value: any) {
        let message: string = 'Error: Invalid value retrieved from Redis: ' +
            value + '.';
        let code: Status = Status.E_540;
        super(message, code);
    }
}

export class EnvVariablesNotAvailable extends ServerError {
    constructor(env_variables: string) {
        let message: string = `Error: ${env_variables} ENV variable not available.`;
        let code: Status = Status.E_541;
        super(message, code);
    }
}
