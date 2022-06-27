import {errorJson, resultJson} from "../../src/utils/response";

describe('resultJson', () => {
    it.each([[{}], [{
        'key1': 'val1',
        'key2': 'val2',
        'key3': true
    }], [45]])('returns the {"result": result} for input %s', (input: any) => {
        let expectedRet = {result: input};
        let ret = resultJson(input);
        expect(expectedRet).toEqual(ret)
    });
});

describe('errorJson', () => {
    it.each([[{}], [{
        'key1': 'val1',
        'key2': 'val2',
        'key3': true
    }], [45]])('returns {"error": error} for input %s', (input: any) => {
        let expectedRet = {error: input};
        let ret = errorJson(input);
        expect(expectedRet).toEqual(ret)
    });
});
