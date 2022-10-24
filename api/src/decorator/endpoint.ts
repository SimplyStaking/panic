import express from 'express';
import { Timeout } from '../constant/server';
import { TimeoutError } from '../constant/server.feedback';
import { ResponseError } from '../v1/entity/io/ResponseData';

export function endpoint() {
    return function (
        target: Object,
        key: string | symbol,
        descriptor: PropertyDescriptor
    ) {

        const child = descriptor.value.bind(target);
        descriptor.value = (...args) => {
            const req: express.Request = args[0];
            const res: express.Response = args[1];

            try {

                let timeout = Timeout.MAX;
                if (req.query.timeout) {
                    timeout = parseInt(req.query.timeout as string) * 1000;
                    if (timeout < Timeout.MIN) {
                        timeout = Timeout.MIN;
                    }
                    req.setTimeout(timeout, () => {
                        const error = new TimeoutError();
                        const response = new ResponseError(res, error);
                        response.send();

                        //to cancel the request
                        res.locals.cancel = true;
                    });
                }

                return child.apply(this, args);
            } catch (err: any) {
                if (err instanceof TimeoutError) {
                    const response = new ResponseError(res, err);
                    response.send();
                }
            }
        }
    };
}