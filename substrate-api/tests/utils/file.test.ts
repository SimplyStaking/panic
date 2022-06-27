import {readFile} from "../../src/utils/file";
import {MissingFile} from "../../src/errors/server";

const fs = require('fs');

let testFilePath = 'testFilePath';

describe('readFile', () => {
    it('reads and returns file if it exists',
        () => {
            // In this test we will mock readFileSync by making it return a
            // dummy file, thus assuming that it works as intended if given a
            // good file path.
            let dummyFile = Buffer.alloc(4);
            let readFileSyncMock = jest.spyOn(
                fs, 'readFileSync'
            ).mockReturnValue(dummyFile);

            let ret = readFile(testFilePath);
            expect(ret).toEqual(dummyFile);

            // Clear mock due to upcoming tests
            readFileSyncMock.mockRestore()
        });
    it('throws unrecognised error if raised by readFileSync',
        () => {
            // Generate error from readFileSync
            let readFileSyncMock = jest.spyOn(
                fs, 'readFileSync'
            ).mockImplementation(
                () => {
                    throw new Error();
                }
            );
            expect(() => {
                readFile(testFilePath)
            }).toThrowError(new Error());

            // Restore the original implementation of readFileSync due to other
            // tests
            readFileSyncMock.mockRestore()
        });
    it('throws MissingFile error if file cannot be found',
        () => {
            // We will assume that the file won't be found if we give a non
            // existing file path.
            expect(() => {
                readFile(testFilePath)
            }).toThrowError(new MissingFile(testFilePath))
        });
});
