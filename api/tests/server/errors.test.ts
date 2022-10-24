import {
    CouldNotRetrieveDataFromMongo,
    CouldNotRetrieveDataFromRedis,
    InvalidBaseChains,
    InvalidEndpoint,
    InvalidJsonSchema,
    InvalidParameterValue,
    InvalidValueRetrievedFromRedis,
    MissingFile,
    MissingKeysInBody,
    MongoClientNotInitialised,
    RedisClientNotInitialised
} from "../../src/constant/errors";
import { RedisError } from "redis";
import { baseChains } from "../../src/constant/server";

describe('Server Errors have correct message and code', () => {
    it('MissingFile', () => {
        const testFilePath: string = 'testFilePath';
        const expectedMessage: string = 'Error: Cannot find testFilePath.';
        const expectedCode: number = 530;
        const actualError = new MissingFile(testFilePath);
        expect(actualError.message).toBe(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });

    it('InvalidEndpoint', () => {
        const endpoint: string = 'testEndpoint';
        const expectedMessage: string = 'Error: \'testEndpoint\' ' +
            'is an invalid endpoint.';
        const expectedCode: number = 531;
        const actualError = new InvalidEndpoint(endpoint);
        expect(actualError.message).toBe(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });

    it('MissingKeysInBody', () => {
        const testKey1: string = 'testKey1';
        const testKey2: string = 'testKey2';
        const expectedMessage: string = 'Error: Missing key(s) testKey1, ' +
            'testKey2 in body.';
        const expectedCode: number = 532;
        const actualError = new MissingKeysInBody(testKey1, testKey2);
        expect(actualError.message).toBe(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });

    it('RedisClientNotInitialised', () => {
        const expectedMessage: string = 'Error: Redis client not initialised.';
        const expectedCode: number = 533;
        const actualError = new RedisClientNotInitialised();
        expect(actualError.message).toBe(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });

    it('CouldNotRetrieveDataFromRedis', () => {
        const testError: RedisError = new RedisError('Test Error');
        const expectedMessage: string = 'Error: ' + testError.name +
            ' retrieved from Redis: ' + testError.message + '.';
        const expectedCode: number = 534;
        const actualError = new CouldNotRetrieveDataFromRedis(testError);
        expect(actualError.message).toBe(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });

    it('MongoClientNotInitialised', () => {
        const expectedMessage: string = 'Error: Mongo client not initialised.';
        const expectedCode: number = 535;
        const actualError = new MongoClientNotInitialised();
        expect(actualError.message).toBe(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });

    it('CouldNotRetrieveDataFromMongo', () => {
        const expectedMessage: string = 'Error: Could not retrieve data ' +
            'from Mongo.';
        const expectedCode: number = 536;
        const actualError = new CouldNotRetrieveDataFromMongo();
        expect(actualError.message).toBe(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });

    it('InvalidBaseChains', () => {
        const testBaseChain1: string = 'testBaseChain1';
        const testBaseChain2: string = 'testBaseChain2';
        const expectedMessage: string = 'Error: Invalid base chain(s) ' +
            'testBaseChain1, testBaseChain2. Please enter a list containing ' +
            'some of these values: ' + baseChains.join(', ') + '.';
        const expectedCode: number = 537;
        const actualError = new InvalidBaseChains(testBaseChain1,
            testBaseChain2);
        expect(actualError.message).toBe(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });

    it('InvalidJsonSchema', () => {
        const testWhichJson: string = 'testJson';
        const expectedMessage: string = 'Error: testJson does not obey ' +
            'the required schema.';
        const expectedCode: number = 538;
        const actualError = new InvalidJsonSchema(testWhichJson);
        expect(actualError.message).toBe(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });

    it('InvalidParameterValue', () => {
        const testParameter: string = 'testParameter';
        const expectedMessage: string = 'Error: An invalid value was given ' +
            'to testParameter.';
        const expectedCode: number = 539;
        const actualError = new InvalidParameterValue(testParameter);
        expect(actualError.message).toBe(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });

    it('InvalidValueRetrievedFromRedis', () => {
        const testValue: string = 'testValue';
        const expectedMessage: string = 'Error: Invalid value retrieved from ' +
            'Redis: ' + testValue + '.';
        const expectedCode: number = 540;
        const actualError = new InvalidValueRetrievedFromRedis(testValue);
        expect(actualError.message).toBe(expectedMessage);
        expect(actualError.code).toBe(expectedCode);
    });
});
