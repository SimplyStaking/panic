import {callApiV1EndpointWithFeedback} from "../api";
import {raiseToast} from "../helpers";

// Some mocks
raiseToast = jest.fn();
fetch = jest.fn();
const successReturn = {result: 'someResult', ok: true};
const failReturn = {result: 'someResult', ok: false};
const mockSuccessReturn = jest.fn().mockImplementation(
    (..._) => successReturn
);
const mockFailReturn = jest.fn().mockImplementation(
    (..._) => failReturn
);
const mockRaiseException = jest.fn().mockImplementation(
    (..._) => {
        throw new Error('test')
    });

afterEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
});

describe('callApiV1EndpointWithFeedback() function', () => {

    // Some dummy variables
    const toastSuccessMsg = "Test operation successful";
    const toastErrorMsg = "Test operation failed";
    const requestProperties = {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({a: 1, b: 'Textual content'})
    };
    const endpoint = 'server/testEndpoint';

    it('raises success toast if API call successful', async () => {
        fetch = mockSuccessReturn;
        await callApiV1EndpointWithFeedback(
            toastSuccessMsg, toastErrorMsg, endpoint, requestProperties);

        // Check that the toast creation function was called correctly.
        expect(raiseToast).toHaveBeenCalledTimes(1);
        expect(raiseToast).toHaveBeenCalledWith(toastSuccessMsg);
    });

    it('raises error toast if API call raises exception',
        async () => {
            fetch = mockRaiseException;
            await callApiV1EndpointWithFeedback(
                toastSuccessMsg, toastErrorMsg, endpoint, requestProperties);

            // Check that the toast creation function was called correctly.
            expect(raiseToast).toHaveBeenCalledTimes(1);
            expect(raiseToast).toHaveBeenCalledWith(
                toastErrorMsg, 2000, "danger")
        });

    it('raises error toast if API call returns error', async () => {
        fetch = mockFailReturn
        await callApiV1EndpointWithFeedback(
            toastSuccessMsg, toastErrorMsg, endpoint, requestProperties);

        // Check that the toast creation function was called correctly.
        expect(raiseToast).toHaveBeenCalledTimes(1);
        expect(raiseToast).toHaveBeenCalledWith(
            toastErrorMsg, 2000, "danger");
    });

    it('returns [response, false] if API call successful',
        async () => {
        fetch = mockSuccessReturn;
        const [actualResponse, actualCallFailed] =
            await callApiV1EndpointWithFeedback(
                toastSuccessMsg, toastErrorMsg, endpoint, requestProperties);

        expect(actualResponse).toEqual(successReturn);
        expect(actualCallFailed).toEqual(false);
    });

    it('returns [response, true] if API call returns error',
        async () => {
            fetch = mockFailReturn
            const [actualResponse, actualCallFailed] =
                await callApiV1EndpointWithFeedback(
                    toastSuccessMsg, toastErrorMsg, endpoint, requestProperties);

            expect(actualResponse).toEqual(failReturn);
            expect(actualCallFailed).toEqual(true);
        });

    it('returns [undefined, true] if API call raises exception',
        async () => {
            fetch = mockRaiseException;
            const [actualResponse, actualCallFailed] =
                await callApiV1EndpointWithFeedback(
                    toastSuccessMsg, toastErrorMsg, endpoint, requestProperties);

            expect(actualResponse).toBeUndefined();
            expect(actualCallFailed).toEqual(true);
        });
});
