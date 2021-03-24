import {BackendErrorCode} from './types'

class BackendError extends Error {
    code: BackendErrorCode;

    constructor(message: string, code: BackendErrorCode) {
        super(message);
        this.code = code;
    }
}

export class MissingFile extends BackendError {
    constructor(filePath: string) {
        let message: string = `Cannot find ${filePath}.`;
        let code: BackendErrorCode = BackendErrorCode.E_530;
        super(message, code)
    }
}

export class InvalidEndpoint extends BackendError {
    constructor(endpoint: string) {
        let message: string = `'${endpoint}' is an invalid endpoint.`;
        let code: BackendErrorCode = BackendErrorCode.E_531;
        super(message, code)
    }
}
