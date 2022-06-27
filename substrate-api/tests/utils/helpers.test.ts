import {missingValues} from "../../src/utils/helpers";

describe('missingValues', () => {
    it.each([
        [{
            'key1': 0,
            'key2': undefined,
            'key3': null,
            'key4': 'test_string',
            'key5': 34,
            'key6': false,
            'key7': true
        }, ['key2', 'key3']],
        [{}, []]
    ])('returns key names with values undefined and null. Input %s, expected ' +
        'output %s', (testObject, expectedReturn) => {
        let actualRet = missingValues(testObject);
        expect(expectedReturn).toEqual(actualRet)
    });
});
