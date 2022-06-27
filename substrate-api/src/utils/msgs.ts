export const apiCallFail = (call: string) => {
    return `API call ${call} failed.`
};

export const apiCallTimeoutFail = (call: string) => {
    return apiCallFail(call) + ' Call took too much time to execute.';
};
