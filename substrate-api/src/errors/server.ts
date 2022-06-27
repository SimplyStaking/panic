// Errors that may be raised by the server

export enum ServerErrorCode {
    E_530 = 530,
    E_531 = 531,
    E_532 = 532,
    E_533 = 533,
    E_534 = 534
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
        let message: string = `Cannot find ${filePath}.`;
        let code: ServerErrorCode = ServerErrorCode.E_530;
        super(message, code);
    }
}

export class InvalidEndpoint extends ServerError {
    constructor(endpoint: string) {
        let message: string = `${endpoint} is an invalid endpoint.`;
        let code: ServerErrorCode = ServerErrorCode.E_531;
        super(message, code);
    }
}

export class CouldNotInitialiseConnection extends ServerError {
    constructor(url: string) {
        let message: string = `Could not initialise connection with ${url}.`;
        let code: ServerErrorCode = ServerErrorCode.E_532;
        super(message, code);
    }
}

export class LostConnectionWithNode extends ServerError {
    constructor(url: string) {
        let message: string = `Lost connection with node ${url}.`;
        let code: ServerErrorCode = ServerErrorCode.E_533;
        super(message, code);
    }
}

export class MissingKeysInQuery extends ServerError {
    constructor(...keys: string[]) {
        let message: string = `Missing key(s) ${keys.join(', ')} in query.`;
        let code: ServerErrorCode = ServerErrorCode.E_534;
        super(message, code);
    }
}
