import {apiCallFail, apiCallTimeoutFail} from "../../src/utils/msgs";

describe('apiCallTimeoutFail', () => {
    it('returns correct message',
        () => {
            let testCall = 'testCall';
            let ret = apiCallTimeoutFail(testCall);
            let expectedRet = `API call ${testCall} failed. Call took too ` +
                'much time to execute.';
            expect(expectedRet).toMatch(ret)
        });
});

describe('apiCallFail', () => {
    it('returns correct message',
        () => {
            let testCall = 'testCall';
            let ret = apiCallFail(testCall);
            let expectedRet = `API call ${testCall} failed.`;
            expect(expectedRet).toMatch(ret)
        });
});
