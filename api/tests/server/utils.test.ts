import {
    allElementsInList,
    allElementsInListHaveTypeString,
    fulfillWithTimeLimit,
    getElementsNotInList,
    missingValues,
    resultJson,
    toBool,
    verifyNodeExporterPing,
    verifyPrometheusPing
} from "../../src/server/utils";

describe('resultJson', () => {
    it.each([
        ['true'], [123], [{test: 'test'}], [[1, 2, 3]]
    ])('Should return a wrapped object with %s as value (result)',
        (value: any) => {
            const ret: any = resultJson(value);
            expect(ret).toEqual({result: value});
        });
});

describe('errorJson', () => {
    it.each([
        ['true'], [123], [{test: 'test'}], [[1, 2, 3]]
    ])('Should return a wrapped object with %s as value (error)',
        (value: any) => {
            const ret: any = resultJson(value);
            expect(ret).toEqual({result: value});
        });
});

describe('toBool', () => {
    it.each([
        ['true'], ['yes'], ['y']
    ])('Should return true when passing %s',
        (booleanString: string) => {
            const ret: boolean = toBool(booleanString);
            expect(ret).toEqual(true);
        });

    it.each([
        ['false'], ['no'], ['n']
    ])('Should return false when passing %s',
        (booleanString: string) => {
            const ret: boolean = toBool(booleanString);
            expect(ret).toEqual(false);
        });
});

describe('missingValues', () => {
    it.each([
        [['test1'], {test1: null}],
        [['test1'], {test1: undefined}],
        [['test1'], {test1: null, test2: {}}],
        [['test1', 'test2'], {test1: null, test2: null}],
        [['test3'], {test1: 'a', test2: 1, test3: null}],
        [['test1', 'test2', 'test3'], {
            test1: null,
            test2: undefined,
            test3: undefined
        }],
        [['test1', 'test3'], {test1: null, test2: {test: 1}, test3: null}],
    ])('Should return %s when passing %s',
        (listOfMissingValues: string[], object: any) => {
            const ret: string[] = missingValues(object)
            expect(ret).toEqual(listOfMissingValues);
        });
});

describe('allElementsInList', () => {
    it.each([
        [[1, 2, 3], [1, 2, 3]],
        [[2], [1, 2]],
        [['test2', 'test'], ['test', 'test2']],
        [[null, 1], ['test', null, 1]],
    ])('Should return true when %s are all in %s',
        (elements: any[], list: any[]) => {
            const ret: boolean = allElementsInList(elements, list)
            expect(ret).toEqual(true);
        });

    it.each([
        [[3, 1], [1, 2]],
        [[1, 2, 3], [4, 5, 6]],
        [['test', 'test3'], ['test2', 'test']],
        [[null, 1, 'test'], ['test', 1]],
    ])('Should return false when %s are not all in %s',
        (elements: any[], list: any[]) => {
            const ret: boolean = allElementsInList(elements, list)
            expect(ret).toEqual(false);
        });
});

describe('getElementsNotInList', () => {
    it.each([
        [[3], [3, 1], [1, 2]],
        [[1, 2, 3], [1, 2, 3], [4, 5, 6]],
        [['test3'], ['test', 'test3'], ['test2', 'test']],
        [[null], [null, 1, 'test'], ['test', 1]],
    ])('Should return %s when %s and %s are passed',
        (listRet: any[], elements: any[], list: any[]) => {
            const ret: any[] = getElementsNotInList(elements, list)
            expect(ret).toEqual(listRet);
        });
});

describe('allElementsInListHaveTypeString', () => {
    it.each([
        [[]], [['test', 'test2']], [['a', 'b', 'c']]
    ])('Should return true when all elements in %s are strings',
        (list: any[]) => {
            const ret: boolean = allElementsInListHaveTypeString(list)
            expect(ret).toEqual(true);
        });

    it.each([
        [[1, 2, 3]], [['test', 1]], [['test', null]]
    ])('Should return false when not all elements in %s are strings',
        (list: any[]) => {
            const ret: boolean = allElementsInListHaveTypeString(list)
            expect(ret).toEqual(false);
        });
});

describe('verifyPrometheusPing', () => {
    it.each([
        ['tendermint_consensus_height', 'cosmos'],
        ['max_unconfirmed_blocks[test]', 'chainlink'],
        ['testing\nmax_unconfirmed_blocks 123', 'chainlink'],
        ['tendermint_consensus_height[test]\ntest_metric', 'cosmos'],
        ['', 'other_chain'],
    ])('Should return true when metric of a given base chain is in prometheus ping data',
        (prometheusPingData: string, baseChain: string) => {
            const ret: boolean = verifyPrometheusPing(prometheusPingData, baseChain);
            expect(ret).toEqual(true);
        });

    it.each([
        ['', 'cosmos'],
        ['testing_metric', 'chainlink'],
        ['testing_metric[test]\ntesting_metric', 'cosmos'],
    ])('Should return false when metric of a given base chain is not in prometheus ping data',
        (prometheusPingData: string, baseChain: string) => {
            const ret: boolean = verifyPrometheusPing(prometheusPingData, baseChain);
            expect(ret).toEqual(false);
        });
});

describe('verifyNodeExporterPing', () => {
    it.each([
        ['node_cpu_seconds_total'],
        ['node_cpu_seconds_total\ntesting'],
        ['testing\nnode_cpu_seconds_total'],
        ['testing\nnode_cpu_seconds_total 123'],
    ])('Should return true when node_cpu_seconds_total is in node exporter ping data',
        (nodeExporterPingData: string) => {
            const ret: boolean = verifyNodeExporterPing(nodeExporterPingData);
            expect(ret).toEqual(true);
        });

    it.each([
        [''],
        ['testing_metric'],
        ['testing_metric[test]\ntesting_metric'],
        ['node_cpu_seconds_total[test]'],
    ])('Should return false when node_cpu_seconds_total is not in node exporter ping data',
        (nodeExporterPingData: string) => {
            const ret: boolean = verifyNodeExporterPing(nodeExporterPingData);
            expect(ret).toEqual(false);
        });
});

describe('fulfillWithTimeLimit', () => {
    it.each([
        [new Promise((resolve, _reject) => {
            resolve(1);
        }), 100],
        [new Promise((resolve, _reject) => {
            setTimeout(() => {
                resolve(1);
            }, 1);
        }), 100],
        [new Promise((resolve, _reject) => {
            setTimeout(() => {
                resolve(1);
            }, 50);
        }), 100],
        [new Promise((resolve, _reject) => {
            setTimeout(() => {
                resolve(1);
            }, 99);
        }), 100],
    ])('Should return task\'s result if task finishes within time limit.',
        (promise: Promise<any>, timeLimit: number) => {
            const ret = fulfillWithTimeLimit(promise, timeLimit, null);
            expect(ret).not.toEqual(null);
        });

    it.each([
        [new Promise((resolve, _reject) => {
            resolve(100);
        }), 1],
        [new Promise((resolve, _reject) => {
            setTimeout(() => {
                resolve(1);
            }, 100);
        }), 50],
        [new Promise((resolve, _reject) => {
            setTimeout(() => {
                resolve(1);
            }, 100);
        }), 99],
        [new Promise((resolve, _reject) => {
            setTimeout(() => {
                resolve(1);
            }, 100);
        }), 0],
    ])('Should return failure value if task did not finish within time limit.',
        (promise: Promise<any>, timeLimit: number) => {
            const ret = fulfillWithTimeLimit(promise, timeLimit, null);
            expect(ret).not.toEqual(null);
        });
});
