import Timeout = require('await-timeout');

export const callFnWithTimeoutSafely = async (
    callback: Function, params: any[], timeout: number,
    returnIfTimeoutExceeded: any
) => {
    const timer = new Timeout();
    try {
        return await Promise.race([
            callback.apply(this, params),
            timer.set(timeout, returnIfTimeoutExceeded)
        ]);
    } finally {
        timer.clear();
    }
};

