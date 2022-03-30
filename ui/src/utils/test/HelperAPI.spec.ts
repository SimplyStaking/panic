import {HelperAPI} from "../helpers";

describe('arrayEquals() function', () => {
    it('should return true if arrays are equal', async () => {
        const arrays: any[][][] = [[[], []], [[1, 2, 3], [1, 2, 3]], [['a', 'b', 'c'], ['a', 'b', 'c']]];

        for (const index in arrays) {
            const result: boolean = HelperAPI.arrayEquals(arrays[index][0], arrays[index][1]);
            expect(result).toEqual(true);
        }
    });

    it('should return false if arrays are not equal', async () => {
        const arrays: any[][][] = [[[1, 2, 3], ['1', '2', '3']], [[1, 2, 3], [3, 2, 1]], [[1, 2, 3], [1, 2, 3, 4]]];

        for (const index in arrays) {
            const result: boolean = HelperAPI.arrayEquals(arrays[index][0], arrays[index][1]);
            expect(result).toEqual(false);
        }
    });
});

describe('dateTimeStringToTimestamp() function', () => {
    it('should return the correct timestamp in seconds for various timestamps in string format', async () => {
        const timestampStrings: string[] = ['2021-11-08T14:57:00+00:00', '2025-01-01T11:11:00+00:00'];
        const expectedTimestampValues: number[] = [1636383420, 1735729860];

        for (const index in timestampStrings) {
            const timestamp: number = HelperAPI.dateTimeStringToTimestamp(timestampStrings[index]);
            const expectedTimestamp: number = expectedTimestampValues[index];

            expect(timestamp).toEqual(expectedTimestamp);
        }
    });
});

describe('getCurrentTimestamp() function', () => {
    it('should return the current timestamp in seconds', async () => {
        expect(Math.round(Date.now() / 1000)).toEqual(HelperAPI.getCurrentTimestamp());
    });
});

describe('formatBytes() function', () => {
    it('should return the correct string representation to 2 decimal places for various byte values', async () => {
        const byteValuesStrings: string[] = ['100', '1024', '10240000', '1073741824', '1152921504606847000'];
        const expectedStringValues: string[] = ['100 Bytes', '1 KB', '9.77 MB', '1 GB', '1 EB'];

        for (const index in byteValuesStrings) {
            const stringValue: string = HelperAPI.formatBytes(byteValuesStrings[index]);
            const expectedStringValue: string = expectedStringValues[index];

            expect(stringValue).toEqual(expectedStringValue);
        }
    });

    it('should return the correct string representation to 3 decimal places for various byte values', async () => {
        const byteValuesStrings: string[] = ['5207', '5210', '682123855'];
        const expectedStringValues: string[] = ['5.085 KB', '5.088 KB', '650.524 MB'];

        for (const index in byteValuesStrings) {
            const stringValue: string = HelperAPI.formatBytes(byteValuesStrings[index], 3);
            const expectedStringValue: string = expectedStringValues[index];

            expect(stringValue).toEqual(expectedStringValue);
        }
    });

    it('should return the correct string representation to 4 decimal places for various byte values', async () => {
        const byteValuesStrings: string[] = ['5151', '682123950', '2684495956'];
        const expectedStringValues: string[] = ['5.0303 KB', '650.5241 MB', '2.5001 GB'];

        for (const index in byteValuesStrings) {
            const stringValue: string = HelperAPI.formatBytes(byteValuesStrings[index], 4);
            const expectedStringValue: string = expectedStringValues[index];

            expect(stringValue).toEqual(expectedStringValue);
        }
    });
});
