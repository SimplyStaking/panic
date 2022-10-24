import express from "express";
import {Document} from "mongoose";

import {Status} from "../../../constant/server";
import {ServerError} from "../../../constant/server.feedback";
import {ObjectUtil} from "../../../util/ObjectUtil";
import {IMessage} from "./IMessage";

/**
 * Response generic behavior Handler
 */
abstract class ResponseData<T> {

    public messages: Array<IMessage> = [];

    constructor(protected res: express.Response, public status: number) {
        res.status(status);
    }

    /**
     * Add one Message to Response
     */
    public addMessage(message: IMessage): ResponseData<T> {
        this.messages.push(message);
        return this;
    }

    abstract send(data: T): void;
}

/**
 * Response Error Handler
 */
export class ResponseError extends ResponseData<void> {
    constructor(res: express.Response, error: ServerError) {
        if (!error.status) {
            throw new Error("Please inform status code!");
        }

        super(res, error.status);
        delete error.status;

        this.addMessage(error)
    }

    public async addMongooseErrors(model: Document): Promise<void> {
        try {
            await model.validate();
        } catch (err) {
            console.error(err);
        } finally {
            for (const key in model.errors) {
                const msg = model.errors[key].message + ' on ' + model.errors[key].path;
                this.addMessage(new ServerError(key, msg));
            }
        }
    }

    public send(): void {
        this.res.send({
            status: this.status,
            messages: this.messages
        });
    }
}

/**
 * Response Error Handler
 */
export class ResponseSuccess<T> extends ResponseData<T> {

    constructor(res: express.Response) {
        super(res, Status.SUCCESS);
    }

    /**
     * Send response to api
     *
     * @param result The result content
     */
    public send(result?: any): void {

        if (result === undefined) {
            this.res.send();
            return;
        }

        if (result instanceof Document) {
            result = ObjectUtil.deepSnakeToCamel(result.toJSON());
        }

        if (Array.isArray(result)) {
            result = result.map(x => ObjectUtil.deepSnakeToCamel(x.toJSON()));
        }

        if (this.messages.length === 0) {
            delete this.messages;
        }

        this.res.send({
            status: this.status,
            result: result,
            messages: this.messages
        });
    }
}

/**
 * Response No Content Handler
 */
export class ResponseNoContent<T> extends ResponseData<T> {

    constructor(res: express.Response) {
        super(res, Status.NO_CONTENT);
    }

    /**
     * Send response to api
     */
    public send(): void {
        this.res.send();
    }
}
