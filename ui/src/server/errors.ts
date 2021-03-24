import {UIServerErrorCode} from './types'
import {RedisError} from "redis";

// Server errors

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

// Redis Errors

export class RedisConnectionRefused extends RedisError {
    constructor() {
        super('The redis server refused the connection.');
    }
}

// Other errors

export class MaxRetryTimeExceeded extends Error {
    constructor() {
        super('Retry time exceeded.');
    }
}
