import {
    CouldNotInitialiseConnection,
    InvalidEndpoint,
    LostConnectionWithNode,
    MissingFile,
    MissingKeysInQuery
} from "../../src/errors/server";

describe('Server Errors have correct message and code', () => {
    it('MissingFile', () => {
        let testFilePath = 'testFilePath';
        let expectedMessage = 'Cannot find testFilePath.';
        let expectedCode = 530;
        let actualError = new MissingFile(testFilePath);
        expect(actualError.message).toMatch(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });
    it('InvalidEndpoint', () => {
        let endpoint = 'testEndpoint';
        let expectedMessage = 'testEndpoint is an invalid endpoint.';
        let expectedCode = 531;
        let actualError = new InvalidEndpoint(endpoint);
        expect(actualError.message).toMatch(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });
    it('CouldNotInitialiseConnection', () => {
        let url = 'testUrl';
        let expectedMessage = 'Could not initialise connection with testUrl.';
        let expectedCode = 532;
        let actualError = new CouldNotInitialiseConnection(url);
        expect(actualError.message).toMatch(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });
    it('LostConnectionWithNode', () => {
        let url = 'testUrl';
        let expectedMessage = 'Lost connection with node testUrl.';
        let expectedCode = 533;
        let actualError = new LostConnectionWithNode(url);
        expect(actualError.message).toMatch(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });
    it('MissingKeysInQuery', () => {
        let keys = ['key1', 'key2', 'key3'];
        let expectedMessage = 'Missing key(s) key1, key2, key3 in query.';
        let expectedCode = 534;
        let actualError = new MissingKeysInQuery(...keys);
        expect(actualError.message).toMatch(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });
});
