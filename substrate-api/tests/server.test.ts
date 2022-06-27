import request from "supertest";

import {app, server} from "../src/server";
import {
    CouldNotInitialiseConnection,
    InvalidEndpoint,
    LostConnectionWithNode,
    MissingKeysInQuery
} from "../src/errors/server";
import {TestApiPromise, TestWsProvider} from "./test-utils";
import {WsInterfacesManager} from "../src/utils/api_interface";

const query = require("../src/routes/query");
const derive = require("../src/routes/derive");
const rpc = require("../src/routes/rpc");
const custom = require("../src/routes/custom");
const helpers = require("../src/utils/helpers");

let testWsUrl = 'testWsUrl';
let testWsProvider: TestWsProvider;
let testApiPromise: TestApiPromise;

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
beforeEach(() => {
    jest.clearAllMocks();
    testWsProvider = new TestWsProvider(testWsUrl);
    testApiPromise = new TestApiPromise(testWsUrl);
});

describe('Server Defaults', () => {
    it.each([
        ['/'],
        ['/api/bad-endpoint']
    ])('Should return InvalidEndpoint if GET request %s',
        async (endpoint: string) => {
            let expectedReturn = new InvalidEndpoint(endpoint);
            const res = await request(app).get(endpoint);
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({
                'error': {
                    message: expectedReturn.message,
                    code: expectedReturn.code
                }
            });
            server.close()
        });
    it.each([
        ['/'],
        ['/api/bad-endpoint']
    ])('Should return InvalidEndpoint if POST request %s',
        async (endpoint: string) => {
            let expectedReturn = new InvalidEndpoint(endpoint);
            const res = await request(app).post(endpoint);
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({
                'error': {
                    message: expectedReturn.message,
                    code: expectedReturn.code
                }
            });
            server.close()
        });
});

describe('GET Routes', () => {
    let testEndpoint = 'testEndpoint';
    it.each([
        [
            '/api/query/grandpa/stalled', {'websocket': testEndpoint}, true,
            query, 'getGrandpaStalled'
        ],
        [
            '/api/query/democracy/depositOf',
            {'websocket': testEndpoint, 'propIndex': 50}, 34634636363, query,
            'getDemocracyDepositOf'
        ],
        [
            '/api/query/democracy/publicPropCount', {'websocket': testEndpoint},
            45, query, 'getDemocracyPublicPropCount'
        ],
        [
            '/api/query/democracy/publicProps', {'websocket': testEndpoint},
            {'prop1': {}, 'prop2': {'data1': 'key1'}}, query,
            'getDemocracyPublicProps'
        ],
        [
            '/api/query/democracy/referendumCount', {'websocket': testEndpoint},
            45, query, 'getDemocracyReferendumCount'
        ],
        [
            '/api/query/democracy/referendumInfoOf',
            {'websocket': testEndpoint, referendumIndex: 45},
            {'info1': 'val', 'info2': 56}, query, 'getDemocracyReferendumInfoOf'
        ],
        [
            '/api/query/session/currentIndex', {'websocket': testEndpoint},
            "0x00004017", query, 'getSessionCurrentIndex'
        ],
        [
            '/api/query/session/validators', {'websocket': testEndpoint},
            ['val1', 'val2', 'val3'], query, 'getSessionValidators'
        ],
        [
            '/api/query/session/disabledValidators',
            {'websocket': testEndpoint}, [45, 56, 43], query,
            'getSessionDisabledValidators'
        ],
        [
            '/api/query/imOnline/authoredBlocks',
            {
                'websocket': testEndpoint,
                'sessionIndex': 45,
                'accountId': 'testVal'
            }, 2, query, 'getImOnlineAuthoredBlocks'
        ],
        [
            '/api/query/imOnline/receivedHeartbeats',
            {
                'websocket': testEndpoint,
                'sessionIndex': 45,
                'authIndex': 45
            }, null, query, 'getImOnlineReceivedHeartbeats'
        ],
        [
            '/api/query/staking/activeEra', {'websocket': testEndpoint}, 46,
            query, 'getStakingActiveEra'
        ],
        [
            '/api/query/staking/erasStakers',
            {
                'websocket': testEndpoint,
                'eraIndex': 45,
                'accountId': 'testAccount'
            }, {total: 4556656, own: 456}, query, 'getStakingErasStakers'
        ],
        [
            '/api/query/staking/erasRewardPoints',
            {
                'websocket': testEndpoint,
                'eraIndex': 45,
            }, {'val1': 46, 'val2': 3465346, 'val3': 45}, query,
            'getStakingErasRewardPoints'
        ],
        [
            '/api/query/staking/ledger',
            {
                'websocket': testEndpoint,
                'accountId': 'testAccount1',
            }, {claimed: [453, 456, 457]}, query, 'getStakingLedger'
        ],
        [
            '/api/query/staking/historyDepth', {'websocket': testEndpoint},
            84, query, 'getStakingHistoryDepth'
        ],
        [
            '/api/query/staking/bonded',
            {
                'websocket': testEndpoint,
                'accountId': 'testAccount1'
            }, 'controller1', query, 'getStakingBonded'
        ],
        [
            '/api/query/system/events',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm'
            }, ['event1', 'event2', 'event3'], query, 'getSystemEvents'
        ],
        [
            '/api/custom/slash/getSlashedAmount',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm',
                'accountId': 'Account1'
            }, 50000000000, custom, 'getSlashGetSlashedAmount'
        ],
        [
            '/api/custom/offline/isOffline',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm',
                'accountId': 'Account1'
            }, true, custom, 'getOfflineIsOffline'
        ],
        [
            '/api/derive/democracy/proposals', {'websocket': testEndpoint},
            {'info1': 'val', 'info2': 56}, derive, 'getDemocracyProposals'
        ],
        [
            '/api/derive/democracy/referendums', {'websocket': testEndpoint},
            {'info1': 'val', 'info2': 56}, derive, 'getDemocracyReferendums'
        ],
        [
            '/api/derive/staking/validators', {'websocket': testEndpoint},
            {
                validators: ['val1', 'val2', 'val3'],
                nextElected: ['val1', 'val2', 'val3']
            }, derive, 'getStakingValidators'
        ],
        [
            '/api/rpc/system/health', {'websocket': testEndpoint},
            {'info1': 'val', 'info2': 56}, rpc, 'getSystemHealth'
        ],
        [
            '/api/rpc/system/properties', {'websocket': testEndpoint},
            {'ss58Format': 2, 'tokenDecimals': [12], 'tokenSymbol': ['KSM']},
            rpc, 'getSystemProperties'
        ],
        [
            '/api/rpc/system/syncState', {'websocket': testEndpoint},
            {'startingBlock': 34, 'currentBlock': 55, 'highestBlock': 55}, rpc,
            'getSystemSyncState'
        ],
        [
            '/api/rpc/chain/getFinalizedHead', {'websocket': testEndpoint},
            "0xeg9j9gsd8hs8d9fs9dgsdg", rpc, 'getChainFinalizedHead'
        ],
        [
            '/api/rpc/chain/getHeader',
            {
                'websocket': testEndpoint,
                'blockHash': "0xs9shd9fsgdfg90sd8dss9dyfg"
            }, {number: 3245345}, rpc, 'getChainGetHeader'
        ],
        [
            '/api/rpc/chain/getBlockHash',
            {
                'websocket': testEndpoint,
                'blockNumber': 3245345
            }, "0xs9shd9fsgdfg90sd8dss9dyfg", rpc, 'getChainGetBlockHash'
        ],
    ])('Should return endpoint result if GET request %s is successful',
        async (endpoint: string, params: any, endpointRet: any,
               apiCallRoute: any, apiCall: string) => {
            // Mock the api call to return a specific value
            let apiCallMock = jest.spyOn(apiCallRoute, apiCall).mockReturnValue(
                endpointRet
            );
            let expectedRet = {'result': endpointRet};

            const res = await request(app).get(endpoint).query(params);

            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual(expectedRet);
            server.close();

            // Restore the original implementation of the api call
            apiCallMock.mockRestore()
        });
    it.each([
        ['/api/query/grandpa/stalled', {'websocket': testEndpoint}],
        ['/api/query/democracy/depositOf',
            {'websocket': testEndpoint, 'propIndex': 50}
        ],
        ['/api/query/democracy/publicPropCount', {'websocket': testEndpoint}],
        ['/api/query/democracy/publicProps', {'websocket': testEndpoint}],
        ['/api/query/democracy/referendumCount', {'websocket': testEndpoint}],
        ['/api/query/democracy/referendumInfoOf',
            {'websocket': testEndpoint, referendumIndex: 45},
        ],
        ['/api/query/session/currentIndex', {'websocket': testEndpoint}],
        ['/api/query/session/validators', {'websocket': testEndpoint}],
        ['/api/query/session/disabledValidators', {'websocket': testEndpoint}],
        ['/api/query/imOnline/authoredBlocks',
            {
                'websocket': testEndpoint,
                'sessionIndex': 45,
                'accountId': 'testVal'
            },
        ],
        ['/api/query/imOnline/receivedHeartbeats',
            {
                'websocket': testEndpoint,
                'sessionIndex': 45,
                'authIndex': 45
            }
        ],
        ['/api/query/staking/activeEra', {'websocket': testEndpoint}],
        ['/api/query/staking/erasStakers',
            {
                'websocket': testEndpoint,
                'eraIndex': 45,
                'accountId': 'testAccount'
            }
        ],
        ['/api/query/staking/erasRewardPoints',
            {'websocket': testEndpoint, 'eraIndex': 45},
        ],
        ['/api/query/staking/ledger',
            {'websocket': testEndpoint, 'accountId': 'testAccount1'},
        ],
        ['/api/query/staking/historyDepth', {'websocket': testEndpoint}],
        ['/api/query/staking/bonded',
            {'websocket': testEndpoint, 'accountId': 'testAccount1'},
        ],
        ['/api/query/system/events',
            {'websocket': testEndpoint, 'blockHash': '0xdf89df9ghsdt83240sdnm'},
        ],
        ['/api/custom/slash/getSlashedAmount',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm',
                'accountId': 'Account1'
            },
        ],
        ['/api/custom/offline/isOffline',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm',
                'accountId': 'Account1'
            }
        ],
        ['/api/derive/democracy/proposals', {'websocket': testEndpoint}],
        ['/api/derive/democracy/referendums', {'websocket': testEndpoint}],
        ['/api/derive/staking/validators', {'websocket': testEndpoint}],
        ['/api/rpc/system/health', {'websocket': testEndpoint}],
        ['/api/rpc/system/properties', {'websocket': testEndpoint}],
        ['/api/rpc/system/syncState', {'websocket': testEndpoint}],
        ['/api/rpc/chain/getFinalizedHead', {'websocket': testEndpoint}],
        ['/api/rpc/chain/getHeader',
            {'websocket': testEndpoint, 'blockHash': "0xs9sgdfg90sd8dss9dyfg"}
        ],
        ['/api/rpc/chain/getBlockHash',
            {'websocket': testEndpoint, 'blockNumber': 3245345},
        ],
    ])('Should return unexpected error if GET request %s fails unexpectedly',
        async (endpoint: string, params: any) => {
            // This test was done for the sake of completion. Note that since
            // the API call is wrapped in a try catch for all errors, this case
            // will very rarely be executed.

            // Raise an unexpected error from the apiCallExecutor function
            let errorMessage = "Unexpected Error";
            let apiCallExecutorMock = jest.spyOn(
                helpers, "apiCallExecutor"
            ).mockImplementation(
                () => {
                    throw new Error(errorMessage);
                }
            );
            let expectedRet = {
                'error': {'message': errorMessage, 'code': null}
            };

            const res = await request(app).get(endpoint).query(params);

            expect(res.statusCode).toEqual(500);
            expect(res.body).toEqual(expectedRet);
            server.close();

            // Restore the original implementation of apiCallExecutor
            apiCallExecutorMock.mockRestore()
        });
    it.each([
        ['/api/query/grandpa/stalled', {}, ['websocket']],
        [
            '/api/query/democracy/depositOf', {'websocket': testEndpoint},
            ['propIndex']
        ],
        ['/api/query/democracy/publicPropCount', {}, ['websocket']],
        ['/api/query/democracy/publicProps', {}, ['websocket']],
        ['/api/query/democracy/referendumCount', {}, ['websocket']],
        [
            '/api/query/democracy/referendumInfoOf', {referendumIndex: 45},
            ['websocket']
        ],
        ['/api/query/session/currentIndex', {}, ['websocket']],
        ['/api/query/session/validators', {}, ['websocket']],
        ['/api/query/session/disabledValidators', {}, ['websocket']],
        ['/api/query/imOnline/authoredBlocks', {'websocket': testEndpoint},
            ['sessionIndex', 'accountId']],
        ['/api/query/imOnline/receivedHeartbeats', {'websocket': testEndpoint},
            ['sessionIndex', 'authIndex']],
        ['/api/query/staking/activeEra', {}, ['websocket']],
        ['/api/query/staking/erasStakers', {'websocket': testEndpoint},
            ['eraIndex', 'accountId']],
        ['/api/query/staking/erasRewardPoints', {'websocket': testEndpoint},
            ['eraIndex']],
        ['/api/query/staking/ledger', {'websocket': testEndpoint},
            ['accountId']],
        ['/api/query/staking/historyDepth', {}, ['websocket']],
        ['/api/query/staking/bonded', {'websocket': testEndpoint},
            ['accountId']],
        ['/api/query/system/events', {'websocket': testEndpoint},
            ['blockHash']],
        ['/api/custom/slash/getSlashedAmount', {'websocket': testEndpoint},
            ['blockHash', 'accountId']],
        ['/api/custom/offline/isOffline', {'websocket': testEndpoint},
            ['blockHash', 'accountId']],
        ['/api/derive/democracy/proposals', {}, ['websocket']],
        ['/api/derive/democracy/referendums', {}, ['websocket']],
        ['/api/derive/staking/validators', {}, ['websocket']],
        ['/api/rpc/system/health', {}, ['websocket']],
        ['/api/rpc/system/properties', {}, ['websocket']],
        ['/api/rpc/system/syncState', {}, ['websocket']],
        ['/api/rpc/chain/getFinalizedHead', {}, ['websocket']],
        ['/api/rpc/chain/getHeader', {'websocket': testEndpoint},
            ['blockHash']],
        ['/api/rpc/chain/getBlockHash', {'websocket': testEndpoint},
            ['blockNumber']],
    ])('Should return MissingKeysInQueryError if GET request %s given ' +
        'params %s in query. Missing params should be %s',
        async (endpoint: string, params: any, missingParams: string[]) => {
            let expectedError = new MissingKeysInQuery(...missingParams);
            let expectedRet = {
                'error': {
                    'message': expectedError.message,
                    'code': expectedError.code
                }
            };

            const res = await request(app).get(endpoint).query(params);

            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual(expectedRet);
            server.close();
        });
    it.each([
        ['/api/query/grandpa/stalled', {'websocket': testEndpoint}],
        ['/api/query/democracy/depositOf',
            {'websocket': testEndpoint, 'propIndex': 50}
        ],
        ['/api/query/democracy/publicPropCount', {'websocket': testEndpoint}],
        ['/api/query/democracy/publicProps', {'websocket': testEndpoint}],
        ['/api/query/democracy/referendumCount', {'websocket': testEndpoint}],
        ['/api/query/democracy/referendumInfoOf',
            {'websocket': testEndpoint, referendumIndex: 45},
        ],
        ['/api/query/session/currentIndex', {'websocket': testEndpoint}],
        ['/api/query/session/validators', {'websocket': testEndpoint}],
        ['/api/query/session/disabledValidators', {'websocket': testEndpoint}],
        ['/api/query/imOnline/authoredBlocks',
            {
                'websocket': testEndpoint,
                'sessionIndex': 45,
                'accountId': 'testVal'
            },
        ],
        ['/api/query/imOnline/receivedHeartbeats',
            {
                'websocket': testEndpoint,
                'sessionIndex': 45,
                'authIndex': 45
            }
        ],
        ['/api/query/staking/activeEra', {'websocket': testEndpoint}],
        ['/api/query/staking/erasStakers',
            {
                'websocket': testEndpoint,
                'eraIndex': 45,
                'accountId': 'testAccount'
            }
        ],
        ['/api/query/staking/erasRewardPoints',
            {'websocket': testEndpoint, 'eraIndex': 45},
        ],
        ['/api/query/staking/ledger',
            {'websocket': testEndpoint, 'accountId': 'testAccount1'},
        ],
        ['/api/query/staking/historyDepth', {'websocket': testEndpoint}],
        ['/api/query/staking/bonded',
            {'websocket': testEndpoint, 'accountId': 'testAccount1'},
        ],
        ['/api/query/system/events',
            {'websocket': testEndpoint, 'blockHash': '0xdf89df9ghsdt83240sdnm'},
        ],
        ['/api/custom/slash/getSlashedAmount',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm',
                'accountId': 'Account1'
            },
        ],
        ['/api/custom/offline/isOffline',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm',
                'accountId': 'Account1'
            }
        ],
        ['/api/derive/democracy/proposals', {'websocket': testEndpoint}],
        ['/api/derive/democracy/referendums', {'websocket': testEndpoint}],
        ['/api/derive/staking/validators', {'websocket': testEndpoint}],
        ['/api/rpc/system/health', {'websocket': testEndpoint}],
        ['/api/rpc/system/properties', {'websocket': testEndpoint}],
        ['/api/rpc/system/syncState', {'websocket': testEndpoint}],
        ['/api/rpc/chain/getFinalizedHead', {'websocket': testEndpoint}],
        ['/api/rpc/chain/getHeader',
            {'websocket': testEndpoint, 'blockHash': "0xs9sgdfg90sd8dss9dyfg"}
        ],
        ['/api/rpc/chain/getBlockHash',
            {'websocket': testEndpoint, 'blockNumber': 3245345},
        ],
    ])('GET request %s should return CouldNotInitialiseConnection ' +
        'error if the server cannot initialise a connection with the node',
        async (endpoint: string, params: any) => {
            // Mock createInterface by making it return true. This means that
            // the server could not initialise a connection with the node.
            let createInterfaceMock = jest.spyOn(
                WsInterfacesManager.prototype, "createInterface"
            ).mockReturnValue(Promise.resolve(true));

            let expectedError = new CouldNotInitialiseConnection(
                params['websocket']);
            let expectedRet = {
                'error': {
                    'message': expectedError.message,
                    'code': expectedError.code
                }
            };

            const res = await request(app).get(endpoint).query(params);

            expect(res.statusCode).toEqual(500);
            expect(res.body).toEqual(expectedRet);
            server.close();

            // Restore the original implementation of createInterface
            createInterfaceMock.mockRestore()
        });
    it.each([
        [
            '/api/query/grandpa/stalled', {'websocket': testEndpoint}, query,
            'getGrandpaStalled'
        ],
        [
            '/api/query/democracy/depositOf',
            {'websocket': testEndpoint, 'propIndex': 50}, query,
            'getDemocracyDepositOf'
        ],
        [
            '/api/query/democracy/publicPropCount', {'websocket': testEndpoint},
            query, 'getDemocracyPublicPropCount'
        ],
        [
            '/api/query/democracy/publicProps', {'websocket': testEndpoint},
            query, 'getDemocracyPublicProps'
        ],
        [
            '/api/query/democracy/referendumCount', {'websocket': testEndpoint},
            query, 'getDemocracyReferendumCount'
        ],
        [
            '/api/query/democracy/referendumInfoOf',
            {'websocket': testEndpoint, referendumIndex: 45}, query,
            'getDemocracyReferendumInfoOf'
        ],
        [
            '/api/query/session/currentIndex', {'websocket': testEndpoint},
            query, 'getSessionCurrentIndex'
        ],
        [
            '/api/query/session/validators', {'websocket': testEndpoint},
            query, 'getSessionValidators'
        ],
        [
            '/api/query/session/disabledValidators',
            {'websocket': testEndpoint}, query, 'getSessionDisabledValidators'
        ],
        [
            '/api/query/imOnline/authoredBlocks',
            {
                'websocket': testEndpoint,
                'sessionIndex': 45,
                'accountId': 'testVal'
            }, query, 'getImOnlineAuthoredBlocks'
        ],
        [
            '/api/query/imOnline/receivedHeartbeats',
            {
                'websocket': testEndpoint,
                'sessionIndex': 45,
                'authIndex': 45
            }, query, 'getImOnlineReceivedHeartbeats'
        ],
        [
            '/api/query/staking/activeEra', {'websocket': testEndpoint}, query,
            'getStakingActiveEra'
        ],
        [
            '/api/query/staking/erasStakers',
            {
                'websocket': testEndpoint,
                'eraIndex': 45,
                'accountId': 'testAccount'
            }, query, 'getStakingErasStakers'
        ],
        [
            '/api/query/staking/erasRewardPoints',
            {
                'websocket': testEndpoint,
                'eraIndex': 45,
            }, query, 'getStakingErasRewardPoints'
        ],
        [
            '/api/query/staking/ledger',
            {'websocket': testEndpoint, 'accountId': 'testAccount1'}, query,
            'getStakingLedger'
        ],
        [
            '/api/query/staking/historyDepth', {'websocket': testEndpoint},
            query, 'getStakingHistoryDepth'
        ],
        [
            '/api/query/staking/bonded',
            {'websocket': testEndpoint, 'accountId': 'testAccount1'}, query,
            'getStakingBonded'
        ],
        [
            '/api/query/system/events',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm'
            }, query, 'getSystemEvents'
        ],
        [
            '/api/custom/slash/getSlashedAmount',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm',
                'accountId': 'Account1'
            }, custom, 'getSlashGetSlashedAmount'
        ],
        [
            '/api/custom/offline/isOffline',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm',
                'accountId': 'Account1'
            }, custom, 'getOfflineIsOffline'
        ],
        [
            '/api/derive/democracy/proposals', {'websocket': testEndpoint},
            derive, 'getDemocracyProposals'
        ],
        [
            '/api/derive/democracy/referendums', {'websocket': testEndpoint},
            derive, 'getDemocracyReferendums'
        ],
        [
            '/api/derive/staking/validators', {'websocket': testEndpoint},
            derive, 'getStakingValidators'
        ],
        [
            '/api/rpc/system/health', {'websocket': testEndpoint}, rpc,
            'getSystemHealth'
        ],
        [
            '/api/rpc/system/properties', {'websocket': testEndpoint}, rpc,
            'getSystemProperties'
        ],
        [
            '/api/rpc/system/syncState', {'websocket': testEndpoint}, rpc,
            'getSystemSyncState'
        ],
        [
            '/api/rpc/chain/getFinalizedHead', {'websocket': testEndpoint}, rpc,
            'getChainFinalizedHead'
        ],
        [
            '/api/rpc/chain/getHeader',
            {'websocket': testEndpoint, 'blockHash': "0xs9shd9fsgdfgd8dss9dy"},
            rpc, 'getChainGetHeader'
        ],
        [
            '/api/rpc/chain/getBlockHash',
            {
                'websocket': testEndpoint,
                'blockNumber': 3245345
            }, rpc, 'getChainGetBlockHash'
        ],
    ])('GET request %s should return unexpected error if API call error ' +
        'and the server still connected with the node',
        async (endpoint: string, params: any, apiCallRoute: any,
               apiCall: string) => {
            // This test will simulate the scenario when the API call raises an
            // error but the server is still connected with the node. Note, by
            // default TestWsProvider has isConnected=True, therefore we don't
            // need to mock the return of isConnected.

            // Make the api call raise an error
            let errorMessage = "API Call Error";
            let apiCallMock = jest.spyOn(
                apiCallRoute, apiCall
            ).mockImplementation(
                () => {
                    throw new Error(errorMessage);
                }
            );
            let expectedRet = {
                'error': {
                    'message': errorMessage,
                    'code': null
                }
            };

            const res = await request(app).get(endpoint).query(params);

            expect(res.statusCode).toEqual(500);
            expect(res.body).toEqual(expectedRet);
            server.close();

            // Restore the original implementation of the API Call
            apiCallMock.mockRestore()
        });
    it.each([
        [
            '/api/query/grandpa/stalled', {'websocket': testEndpoint}, query,
            'getGrandpaStalled'
        ],
        [
            '/api/query/democracy/depositOf',
            {'websocket': testEndpoint, 'propIndex': 50}, query,
            'getDemocracyDepositOf'
        ],
        [
            '/api/query/democracy/publicPropCount', {'websocket': testEndpoint},
            query, 'getDemocracyPublicPropCount'
        ],
        [
            '/api/query/democracy/publicProps', {'websocket': testEndpoint},
            query, 'getDemocracyPublicProps'
        ],
        [
            '/api/query/democracy/referendumCount', {'websocket': testEndpoint},
            query, 'getDemocracyReferendumCount'
        ],
        [
            '/api/query/democracy/referendumInfoOf',
            {'websocket': testEndpoint, referendumIndex: 45}, query,
            'getDemocracyReferendumInfoOf'
        ],
        [
            '/api/query/session/currentIndex', {'websocket': testEndpoint},
            query, 'getSessionCurrentIndex'
        ],
        [
            '/api/query/session/validators', {'websocket': testEndpoint},
            query, 'getSessionValidators'
        ],
        [
            '/api/query/session/disabledValidators',
            {'websocket': testEndpoint}, query, 'getSessionDisabledValidators'
        ],
        [
            '/api/query/imOnline/authoredBlocks',
            {
                'websocket': testEndpoint,
                'sessionIndex': 45,
                'accountId': 'testVal'
            }, query, 'getImOnlineAuthoredBlocks'
        ],
        [
            '/api/query/imOnline/receivedHeartbeats',
            {
                'websocket': testEndpoint,
                'sessionIndex': 45,
                'authIndex': 45
            }, query, 'getImOnlineReceivedHeartbeats'
        ],
        [
            '/api/query/staking/activeEra', {'websocket': testEndpoint}, query,
            'getStakingActiveEra'
        ],
        [
            '/api/query/staking/erasStakers',
            {
                'websocket': testEndpoint,
                'eraIndex': 45,
                'accountId': 'testAccount'
            }, query, 'getStakingErasStakers'
        ],
        [
            '/api/query/staking/erasRewardPoints',
            {
                'websocket': testEndpoint,
                'eraIndex': 45,
            }, query, 'getStakingErasRewardPoints'
        ],
        [
            '/api/query/staking/ledger',
            {'websocket': testEndpoint, 'accountId': 'testAccount1'}, query,
            'getStakingLedger'
        ],
        [
            '/api/query/staking/historyDepth', {'websocket': testEndpoint},
            query, 'getStakingHistoryDepth'
        ],
        [
            '/api/query/staking/bonded',
            {'websocket': testEndpoint, 'accountId': 'testAccount1'}, query,
            'getStakingBonded'
        ],
        [
            '/api/query/system/events',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm'
            }, query, 'getSystemEvents'
        ],
        [
            '/api/custom/slash/getSlashedAmount',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm',
                'accountId': 'Account1'
            }, custom, 'getSlashGetSlashedAmount'
        ],
        [
            '/api/custom/offline/isOffline',
            {
                'websocket': testEndpoint,
                'blockHash': '0xdf89df9ghsd90hsd80ht83240sdnm',
                'accountId': 'Account1'
            }, custom, 'getOfflineIsOffline'
        ],
        [
            '/api/derive/democracy/proposals', {'websocket': testEndpoint},
            derive, 'getDemocracyProposals'
        ],
        [
            '/api/derive/democracy/referendums', {'websocket': testEndpoint},
            derive, 'getDemocracyReferendums'
        ],
        [
            '/api/derive/staking/validators', {'websocket': testEndpoint},
            derive, 'getStakingValidators'
        ],
        [
            '/api/rpc/system/health', {'websocket': testEndpoint}, rpc,
            'getSystemHealth'
        ],
        [
            '/api/rpc/system/properties', {'websocket': testEndpoint}, rpc,
            'getSystemProperties'
        ],
        [
            '/api/rpc/system/syncState', {'websocket': testEndpoint}, rpc,
            'getSystemSyncState'
        ],
        [
            '/api/rpc/chain/getFinalizedHead', {'websocket': testEndpoint}, rpc,
            'getChainFinalizedHead'
        ],
        [
            '/api/rpc/chain/getHeader',
            {'websocket': testEndpoint, 'blockHash': "0xs9shd9fsgdfgd8dss9dy"},
            rpc, 'getChainGetHeader'
        ],
        [
            '/api/rpc/chain/getBlockHash',
            {
                'websocket': testEndpoint,
                'blockNumber': 3245345
            }, rpc, 'getChainGetBlockHash'
        ],
    ])('GET request %s should return LostConnectionWithNode error if ' +
        'API call error and the server is no longer connected with the node',
        async (endpoint: string, params: any, apiCallRoute: any,
               apiCall: string) => {
            // This test will simulate the scenario when the API call raises an
            // error and the server is no longer connected with the node. Note,
            // by default TestWsProvider has isConnected=True, therefore we
            // need to mock it by making it return false.

            // Make the api call raise an error
            let errorMessage = "API Call Error";
            let apiCallMock = jest.spyOn(
                apiCallRoute, apiCall
            ).mockImplementation(
                () => {
                    throw new Error(errorMessage);
                }
            );

            // Make isConnected=False
            let isConnectedMock = jest.spyOn(
                TestWsProvider.prototype, "isConnected", 'get'
            ).mockReturnValue(false);

            let expectedErr = new LostConnectionWithNode(params['websocket']);
            let expectedRet = {
                'error': {
                    'message': expectedErr.message,
                    'code': expectedErr.code
                }
            };

            const res = await request(app).get(endpoint).query(params);

            expect(res.statusCode).toEqual(500);
            expect(res.body).toEqual(expectedRet);
            server.close();

            // Restore the original implementations of the API Call and
            // isConnected
            apiCallMock.mockRestore();
            isConnectedMock.mockRestore()
        });
});
