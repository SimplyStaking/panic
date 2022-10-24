import {IMessage, TypeMessage} from "../v1/entity/io/IMessage";
import {Status} from "./server";

export class ServerError extends Error implements IMessage {

    public status: number;

    constructor(
        public name: string,
        public description: string,
        public type: TypeMessage = "error"
    ) {
        super(description);
    }
}

export class CouldNotRetrieveDataFromDB extends ServerError {
    constructor() {
        const name = 'could_not_retrieve_data';
        super(name, 'Could not retrieve data from Database.');

        this.status = Status.E_536;
    }
}

export class CouldNotRemoveDataFromDB extends ServerError {
    constructor() {
        const name = 'could_not_remove_data';
        super(name, 'Could not remove data from Database.');
        this.status = Status.E_536;
    }
}

export class CouldNotSaveDataToDB extends ServerError {
    constructor() {
        const name = 'could_not_save_data';
        super(name, 'Could not save data to Database.');
        this.status = Status.E_536;
    }
}

export class ValidationDataError extends ServerError {
    constructor() {
        const name = 'validation_data_error';
        super(name, 'Bad Request! Invalid data input.');

        this.status = Status.ERROR;
    }
}

export class NotFoundWarning extends ServerError {
    constructor() {
        const name = 'register_not_found';
        super(name, 'Register not found!', 'warning');

        this.status = Status.NOT_FOUND;
    }
}

export class DuplicateWarning extends ServerError {
    constructor(parameter: string) {
        super(parameter, `Register Duplicated on ${parameter}!`, 'warning');

        this.status = Status.CONFLICT;
    }
}

export class MissingParameterWarning extends ServerError {
    constructor(parameter: string) {
        const name = 'missing_parameter';
        super(name, `There was a missing parameter : ${parameter}`, 'warning');

        this.status = Status.NOT_FOUND;
    }
}

export class TimeoutError extends ServerError {
    constructor() {
        const name = 'timeout_error';
        super(name, 'The server is taking to long to respond, this can be caused by' +
            'either poor connectivity or an error with our servers. Please try again in a while');

        console.error('Request has timed out.');
        this.status = Status.TIMEOUT;
    }
}

export class InvalidIDError extends ServerError {
    constructor(id: string) {
        const name = 'invalid_id';
        super(name, `Your ID ${id} must be a single String of 12 bytes or a string of 24 hex characters`,
            'error');

        this.status = Status.ERROR;
    }
}
