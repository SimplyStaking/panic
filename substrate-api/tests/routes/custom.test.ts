import {
    getOfflineIsOffline,
    getSlashGetSlashedAmount
} from "../../src/routes/custom";
import {TestApiPromise, TestWsProvider} from "../test-utils";
import {ApiPromise} from "@polkadot/api";

const query = require("../../src/routes/query");

let testAccountId = 'testAccount1';
let testBlockHash = 'testBlockHash';
let testWsUrl = 'testWsUrl';
let testWsProvider: TestWsProvider;
let testApiPromise: TestApiPromise;
let apiPromiseInstance: ApiPromise;

// Mock the WsProvider constructor and ApiPromise create function to avoid
// opening connections when testing.
jest.mock('@polkadot/api', () => {
    return {
        WsProvider: jest.fn().mockImplementation((_: string) => {
            return testWsProvider
        }),
        ApiPromise: {
            create: () => {
                return testApiPromise
            }
        },
    };
});

// This is used to clear all mock data after each test
beforeEach(async () => {
    jest.clearAllMocks();
    testWsProvider = new TestWsProvider(testWsUrl);
    testApiPromise = new TestApiPromise(testWsUrl);
    apiPromiseInstance = await ApiPromise.create();
});

describe('getSlashGetSlashedAmount', () => {
    it.each([
        [
            [
                {
                    event: {
                        section: "Staking",
                        method: "Slashed",
                        data: [testAccountId, 400000000]
                    }
                },
                {
                    event: {
                        section: "Staking",
                        method: "Slashed",
                        data: [testAccountId, "0x05000000"]
                    }
                },
                {
                    event: {
                        section: "ImOnline",
                        method: "SomeOffline",
                        data: [testAccountId, "0x05000000"]
                    }
                }
            ], 483886080,
        ],
        [
            [
                {
                    event: {
                        section: "Staking",
                        method: "Rewarded",
                        data: [testAccountId, "0x05000000"]
                    }
                },
                {
                    event: {
                        section: "Staking",
                        method: "StakersElected",
                        data: [testAccountId, "0x05000000"]
                    }
                },
                {
                    event: {
                        section: "ImOnline",
                        method: "SomeOffline",
                        data: [testAccountId, "0x05000000"]
                    }
                }
            ], 0,
        ],
        [[], 0,],
    ])('Returns correct amount if events=%s', async (
        events: any, expectedReturn: number,
    ) => {
        // In this test we will mock the return of getSystemEvents to make sure
        // that getSlashGetSlashedAmount returns the correct slashed amount
        jest.spyOn(query, "getSystemEvents").mockReturnValue(events);

        let actualRet = await getSlashGetSlashedAmount(
            apiPromiseInstance, testBlockHash, testAccountId
        );
        expect(actualRet).toEqual(expectedReturn);
    });
    it('Raises exception if raised by getSystemEvents', async () => {
        // In this test we will simulate the scenario when getSystemEvents
        // throws and exception.
        let errorMessage = "API Call Error";
        jest.spyOn(query, "getSystemEvents").mockImplementation(
            () => {
                throw new Error(errorMessage);
            }
        );
        await expect(
            async () => {
                await getSlashGetSlashedAmount(
                    apiPromiseInstance, testBlockHash, testAccountId
                );
            }
        ).rejects.toThrow(Error);
    });
});

describe('getOfflineIsOffline', () => {
    it.each([
        [
            [
                {
                    event: {
                        section: "Staking",
                        method: "Slashed",
                        data: [testAccountId, "0x05000000"]
                    }
                },
                {
                    event: {
                        section: "ImOnline",
                        method: "SomeOffline",
                        data: [
                            [
                                [
                                    testAccountId,
                                    {
                                        total: 85746767,
                                        own: 34568,
                                    }
                                ]
                            ]
                        ]
                    }
                },
                {
                    event: {
                        section: "Staking",
                        method: "Slashed",
                        data: [testAccountId, "0x05000000"]
                    }
                }
            ], true,
        ],
        [
            [
                {
                    event: {
                        section: "Staking",
                        method: "Rewarded",
                        data: [testAccountId, "0x05000000"]
                    }
                },
                {
                    event: {
                        section: "Staking",
                        method: "StakersElected",
                        data: [testAccountId, "0x05000000"]
                    }
                },
                {
                    event: {
                        section: "Staking",
                        method: "Slashed",
                        data: [testAccountId, "0x05000000"]
                    }
                },
            ], false,
        ],
        [[], false,],
    ])('Returns correct value if events=%s', async (
        events: any, expectedReturn: boolean,
    ) => {
        // In this test we will mock the return of getSystemEvents to make sure
        // that getOfflineIsOffline returns correctly
        jest.spyOn(query, "getSystemEvents").mockReturnValue(events);

        let actualRet = await getOfflineIsOffline(
            apiPromiseInstance, testBlockHash, testAccountId
        );
        expect(actualRet).toEqual(expectedReturn);
    });
    it('Raises exception if raised by getSystemEvents', async () => {
        // In this test we will simulate the scenario when getSystemEvents
        // throws and exception.
        let errorMessage = "API Call Error";
        jest.spyOn(query, "getSystemEvents").mockImplementation(
            () => {
                throw new Error(errorMessage);
            }
        );
        await expect(
            async () => {
                await getOfflineIsOffline(
                    apiPromiseInstance, testBlockHash, testAccountId
                );
            }
        ).rejects.toThrow(Error);
    });
});
