// Make sure that this is at the top of the file since it is required before importing any packages.
process.env.UI_ACCESS_IP = '0.0.0.0';

import {getPrometheusMetricFromBaseChain} from "../src/server/utils";
import {AggregationCursor, Collection, FilterQuery, MongoCallback, MongoClientCommonOption} from 'mongodb';
import {Callback, RedisError} from 'redis';
import {baseChains, PingStatus} from "../src/constant/server";
import request from 'supertest'
import {app, mongoInterval, redisInterval, server} from '../src/server';
import {EnvVariablesNotAvailable, InvalidEndpoint, MissingKeysInBody} from '../src/constant/errors';
import {
    alertsMultipleSourcesEndpointRet,
    alertsMultipleSourcesMongoRet,
    alertsOverviewChainSourceEndpointRet,
    alertsOverviewChainSourceRedisRet,
    alertsOverviewChainSourceWithUniqueIdentifierEndpointRet,
    alertsOverviewChainSourceWithUniqueIdentifierRedisRet,
    alertsOverviewMultipleSourcesEndpointRet,
    alertsOverviewMultipleSourcesRedisRet,
    alertsOverviewSingleDockerHubRepoEndpointRet,
    alertsOverviewSingleDockerHubRepoRedisRet,
    alertsOverviewSingleGitHubRepoEndpointRet,
    alertsOverviewSingleGitHubRepoRedisRet,
    alertsOverviewSingleNodeEndpointRet,
    alertsOverviewSingleNodeRedisRet,
    alertsOverviewSingleSystemEndpointRet,
    alertsOverviewSingleSystemRedisRet,
    alertsSingleSourceEndpointRet,
    alertsSingleSourceMongoRet,
    axiosMock,
    emptyAxiosResponse,
    metricsMultipleSystemsEndpointRet,
    metricsMultipleSystemsMongoRet,
    metricsSingleRepoRedisEndpointRet,
    metricsSingleRepoRedisRet,
    metricsSingleSystemEndpointRet,
    metricsSingleSystemMongoRet,
    metricsSingleSystemRedisEndpointRet,
    metricsSingleSystemRedisRet,
    monitorablesInfoInvalidBaseChainsError,
    monitorablesInfoMultipleSourcesAndBaseChainsEndpointRet,
    monitorablesInfoMultipleSourcesAndBaseChainsMongoRet,
    monitorablesInfoMultipleSourcesEndpointRet,
    monitorablesInfoMultipleSourcesMongoRet,
    monitorablesInfoSingleSourceEndpointRet,
    monitorablesInfoSingleSourceMongoRet,
    noMetricsSingleRepoRedisEndpointRet,
    noMetricsSingleRepoRedisRet,
    noMetricsSingleSystemRedisEndpointRet,
    noMetricsSingleSystemRedisRet,
    parentIdsInvalidSchemaError
} from './test-utils';
import {AxiosResponse} from "axios";
import * as pagerDutyApi from '@pagerduty/pdjs';

const Web3 = require('web3');
const opsgenie = require('opsgenie-sdk');
const twilio = require('twilio');
const nodemailer = require('nodemailer');

// Mongo Mock
let mongoAggregateMockReturn: any[] = [];
let mongoFindMockReturn: any[] = [];
let mongoMockCount: number = 0;

jest.mock('../src/server/mongo', () => {
    return {
        ...jest.requireActual<any>('../src/server/mongo'),
        MongoInterface: jest.fn(() => {
            return {
                client: {
                    db: ((dbName?: string | undefined,
                          options?: MongoClientCommonOption | undefined) => {
                        return {
                            collection: (_name: string,
                                         _callback?:
                                             MongoCallback<Collection<any>> |
                                             undefined) => {
                                return {
                                    countDocuments: (async () => mongoMockCount),
                                    aggregate:
                                        ((_callback:
                                              MongoCallback<AggregationCursor<any>>) => {
                                            return {
                                                toArray: (async ():
                                                    Promise<any[]> => {
                                                    return mongoAggregateMockReturn
                                                })
                                            }
                                        }),
                                    find: ((_query: FilterQuery<any>) => {
                                        return {
                                            toArray: (async ():
                                                Promise<any[]> => {
                                                return mongoFindMockReturn
                                            })
                                        }
                                    })
                                }
                            }
                        }
                    })
                },
                connect: () => {
                    return
                }
            }
        })
    };
});

// Redis Mock
let mgetMockCallbackReply: string[] = [];
let mgetMockCallbackError: Error | null = null;
let hgetallMockCallbackReply: { [p: string]: string } = {};
let hmgetMockCallbackReply: string[] = [];
let execMockCallbackError: Error | null = null;

jest.mock('../src/server/redis', () => {
    return {
        ...jest.requireActual<any>('../src/server/redis'),
        RedisInterface: jest.fn(() => {
            return {
                client: {
                    mget: ((_arg1: string | string[],
                            cb?: Callback<string[]> | undefined) => {
                        if (cb) {
                            cb(mgetMockCallbackError, mgetMockCallbackReply);
                        }
                    }),
                    multi: () => {
                        return {
                            hgetall: ((_key: string, cb?: Callback<{
                                [p: string]: string
                            }> | undefined) => {
                                if (cb) {
                                    cb(null, hgetallMockCallbackReply);
                                }
                            }),
                            hmget: ((_key: string, _arg1: string | string[],
                                     cb?: Callback<string[]> | undefined) => {
                                if (cb) {
                                    cb(null, hmgetMockCallbackReply);
                                }
                            }),
                            exec: ((cb?: Callback<any[]> | undefined) => {
                                if (cb) {
                                    cb(execMockCallbackError, []);
                                }
                            })
                        }
                    }
                },
                connect: () => {
                    return
                }
            }
        })
    };
});

// Axios Mock
jest.mock('axios');

// Web3 mock
jest.mock('web3');

let web3EthGetBlockNumberPromiseResolve: null | number = null;

Web3.providers.HttpProvider.mockImplementation((_url) => null);

Web3.mockImplementation((_provider) => {
    return {
        eth: {
            getBlockNumber: () => {
                return new Promise((resolve, reject) => {
                    web3EthGetBlockNumberPromiseResolve !== null ?
                        resolve(web3EthGetBlockNumberPromiseResolve) : reject({message: 'test'})
                });
            }
        }
    }
});

// Opsgenie SDK Mock
let alertV2CreateMockCallbackError: Error | null = null;

jest.mock('opsgenie-sdk');

opsgenie.alertV2.create.mockImplementation((_data, cb) => {
    cb(alertV2CreateMockCallbackError, null);
})

// Slack Web-Api Mock
let slackMock = {
    chat: {
        postMessage: jest.fn()
    },
};

jest.mock('@slack/web-api', () => {
    return {WebClient: jest.fn(() => slackMock)};
});

// Twilio mock
jest.mock('twilio');

let twilioClientCallsCreateResolve: null | object = null;

twilio.mockImplementation((_accountSid, _authToken) => {
    return {
        calls: {
            create: (_content) => {
                return new Promise((resolve, reject) => {
                    twilioClientCallsCreateResolve !== null ?
                        resolve(twilioClientCallsCreateResolve) : reject({message: 'test'})
                });
            }
        }
    }
});

// nodemailer mock
jest.mock('nodemailer');

let nodemailerVerifyCallbackError: null | Error = null;
let nodemailerSendMailCallbackError: null | Error = null;

nodemailer.createTransport.mockReturnValue({
    verify: (callback) => {
        callback(nodemailerVerifyCallbackError, null);
    },
    sendMail: (_, callback) => {
        callback(nodemailerSendMailCallbackError, null);
    }
});

// This is used to clear all mock data before each test
beforeEach(async () => {
    mongoAggregateMockReturn = [];
    mongoFindMockReturn = [];
    mgetMockCallbackReply = [];
    mgetMockCallbackError = null;
    hgetallMockCallbackReply = {};
    hmgetMockCallbackReply = [];
    execMockCallbackError = null;
    web3EthGetBlockNumberPromiseResolve = null;
    alertV2CreateMockCallbackError = null;
    slackMock = {
        chat: {
            postMessage: jest.fn()
        },
    };
    twilioClientCallsCreateResolve = null;
    nodemailerVerifyCallbackError = null;
    nodemailerSendMailCallbackError = null;

    jest.clearAllMocks();
})

// Used to stop redis and mongo interval processes after all tests finish
afterAll(() => {
    mongoInterval.unref();
    redisInterval.unref();

    server.close();
});

describe('Mongo Monitorables Info POST Route', () => {
    const endpoint = '/server/mongo/monitorablesInfo';

    it.each([
        ['a single base chain which is not in mongo is specified',
            {baseChains: ['cosmos']},
            [],
            {result: {cosmos: {}}}],
        ['a single base chain which is empty in mongo is specified',
            {baseChains: ['cosmos']},
            [{_id: "cosmos"}],
            {result: {cosmos: {}}}],
        ['all base chains specified are not in mongo',
            {baseChains: ['cosmos', 'general', 'chainlink', 'substrate']},
            [],
            {
                result: {
                    cosmos: {}, general: {}, chainlink: {},
                    substrate: {}
                }
            }],
        ['all base chains specified are empty in mongo',
            {baseChains},
            [
                {_id: "cosmos"},
                {_id: "general"},
                {_id: "chainlink"},
                {_id: "substrate"}],
            {
                result: {
                    cosmos: {}, general: {}, chainlink: {},
                    substrate: {}
                }
            }],
        ['all base chains are specified and a single base chain with a' +
        ' single source is in mongo',
            {baseChains},
            monitorablesInfoSingleSourceMongoRet,
            monitorablesInfoSingleSourceEndpointRet],
        ['all base chains are specified and a single base chain with multiple' +
        ' sources is in mongo',
            {baseChains},
            monitorablesInfoMultipleSourcesAndBaseChainsMongoRet,
            monitorablesInfoMultipleSourcesAndBaseChainsEndpointRet],
        ['all base chains are specified and multiple base chains with' +
        ' multiple sources are in mongo',
            {baseChains},
            monitorablesInfoMultipleSourcesMongoRet,
            monitorablesInfoMultipleSourcesEndpointRet]
    ])('Should return correct result and a successful status code if %s',
        async (_: string, body: any, mongoRet: any[],
               endpointRet: any) => {
            mongoFindMockReturn = mongoRet;
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual(endpointRet);
        });

    it.each([
        [532, 'baseChains not specified', {},
            {error: 'Error: Missing key(s) baseChains in body.'}],
        [537, 'invalid base chains are specified', {baseChains: ['test']},
            {error: monitorablesInfoInvalidBaseChainsError}],
    ])('Should return error and %s status code if %s',
        async (statusCode: number, _: string, body: any,
               endpointRet: any) => {
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(statusCode);
            expect(res.body).toEqual(endpointRet);
        });

    it('Should return error and status code 536 if mongo returns an ' +
        'error',
        async () => {
            mongoFindMockReturn = [null];
            const res = await request(app).post(endpoint)
                .send({baseChains: ['cosmos']});
            expect(res.statusCode).toEqual(536);
            expect(res.body)
                .toEqual({
                    error: 'Error: Could not retrieve data from Mongo.'
                });
        });
});

describe('Mongo Alerts POST Route', () => {
    const endpoint = '/server/mongo/alerts';

    it.each([
        ['no chains, severities, or sources are specified',
            {
                chains: [], severities: [], sources: [], minTimestamp: 0,
                maxTimestamp: 5000000000, noOfAlerts: 100
            },
            [],
            {result: {alerts: []}}],
        ['a single chain, all severities, and a single source that has no ' +
        'alerts are specified',
            {
                chains: ['test_chain'],
                severities: ['INFO', 'WARNING', 'CRITICAL', 'ERROR'],
                sources: ['test_source'], minTimestamp: 0,
                maxTimestamp: 5000000000, noOfAlerts: 100
            },
            [],
            {result: {alerts: []}}],
        ['a single chain, all severities, and a single source that has some ' +
        'alerts are specified',
            {
                chains: ['test_chain'],
                severities: ['INFO', 'WARNING', 'CRITICAL', 'ERROR'],
                sources: ['test_source'], minTimestamp: 0,
                maxTimestamp: 5000000000, noOfAlerts: 100
            },
            alertsSingleSourceMongoRet,
            alertsSingleSourceEndpointRet],
        ['multiple chains, all severities, and multiple sources that have ' +
        'some alerts are specified',
            {
                chains: ['test_chain', 'test_chain2'],
                severities: ['INFO', 'WARNING', 'CRITICAL', 'ERROR'],
                sources: ['test_node', 'test_repo'], minTimestamp: 0,
                maxTimestamp: 5000000000, noOfAlerts: 100
            },
            alertsMultipleSourcesMongoRet,
            alertsMultipleSourcesEndpointRet],
    ])('Should return correct result and a successful status code if %s',
        async (_: string, body: any, mongoRet: any[], endpointRet: any) => {
            mongoAggregateMockReturn = mongoRet;
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual(endpointRet);
        });

    it.each([
        [532,
            'chains, severities, sources, minTimestamp, maxTimestamp, and ' +
            'noOfAlerts not specified',
            {},
            {
                error: 'Error: Missing key(s) chains, severities, sources, ' +
                    'minTimestamp, maxTimestamp, noOfAlerts in body.'
            }],
        [532, 'chains not specified',
            {
                severities: [], sources: [], minTimestamp: 0, maxTimestamp: 0,
                noOfAlerts: 1
            },
            {error: 'Error: Missing key(s) chains in body.'}],
        [532, 'severities not specified',
            {
                chains: [], sources: [], minTimestamp: 0, maxTimestamp: 0,
                noOfAlerts: 1
            },
            {error: 'Error: Missing key(s) severities in body.'}],
        [532, 'sources not specified',
            {
                chains: [], severities: [], minTimestamp: 0, maxTimestamp: 0,
                noOfAlerts: 1
            },
            {error: 'Error: Missing key(s) sources in body.'}],
        [532, 'minTimestamp not specified',
            {
                chains: [], severities: [], sources: [], maxTimestamp: 0,
                noOfAlerts: 1
            },
            {error: 'Error: Missing key(s) minTimestamp in body.'}],
        [532, 'maxTimestamp not specified',
            {
                chains: [], severities: [], sources: [], minTimestamp: 0,
                noOfAlerts: 1
            },
            {error: 'Error: Missing key(s) maxTimestamp in body.'}],
        [532, 'noOfAlerts not specified',
            {
                chains: [], severities: [], sources: [], minTimestamp: 0,
                maxTimestamp: 0
            },
            {error: 'Error: Missing key(s) noOfAlerts in body.'}],
        [539, 'invalid chain specified (non-string)',
            {
                chains: ['test_chain', 123], severities: [], sources: [],
                minTimestamp: 0, maxTimestamp: 0, noOfAlerts: 1
            },
            {error: 'Error: An invalid value was given to req.body.chains.'}],
        [539, 'invalid severity specified (non-string)',
            {
                chains: [], severities: ['test_chain', 123], sources: [],
                minTimestamp: 0, maxTimestamp: 0, noOfAlerts: 1
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.severities.'
            }],
        [539, 'invalid source specified (non-string)',
            {
                chains: [], severities: [], sources: ['test_chain', 123],
                minTimestamp: 0, maxTimestamp: 0, noOfAlerts: 1
            },
            {error: 'Error: An invalid value was given to req.body.sources.'}],
        [539, 'invalid severity specified (non-existing)',
            {
                chains: [], severities: ['TEST'], sources: [], minTimestamp: 0,
                maxTimestamp: 0, noOfAlerts: 1
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.severities.'
            }],
        [539, 'invalid minTimestamp specified (string)',
            {
                chains: [], severities: [], sources: [], minTimestamp: 'TEST',
                maxTimestamp: 0, noOfAlerts: 1
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.minTimestamp.'
            }],
        [539, 'invalid maxTimestamp specified (string)',
            {
                chains: [], severities: [], sources: [], minTimestamp: 0,
                maxTimestamp: 'TEST', noOfAlerts: 1
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.maxTimestamp.'
            }],
        [539, 'invalid noOfAlerts specified (string)',
            {
                chains: [], severities: [], sources: [], minTimestamp: 0,
                maxTimestamp: 0, noOfAlerts: 'TEST'
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.noOfAlerts.'
            }],
        [539, 'invalid minTimestamp specified (negative number)',
            {
                chains: [], severities: [], sources: [], minTimestamp: -123,
                maxTimestamp: 0, noOfAlerts: 1
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.minTimestamp.'
            }],
        [539, 'invalid maxTimestamp specified (negative number)',
            {
                chains: [], severities: [], sources: [], minTimestamp: 0,
                maxTimestamp: -123, noOfAlerts: 1
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.maxTimestamp.'
            }],
        [539, 'invalid noOfAlerts specified (negative number)',
            {
                chains: [], severities: [], sources: [], minTimestamp: 0,
                maxTimestamp: 0, noOfAlerts: -123
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.noOfAlerts.'
            }],
        [539, 'invalid noOfAlerts specified (zero)',
            {
                chains: [], severities: [], sources: [], minTimestamp: 0,
                maxTimestamp: 0, noOfAlerts: 0
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.noOfAlerts.'
            }],
    ])('Should return error and %s status code if %s',
        async (statusCode: number, _: string, body: any,
               endpointRet: any) => {
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(statusCode);
            expect(res.body).toEqual(endpointRet);
        });

    it('Should return error and status code 536 if mongo ' +
        'returns an error',
        async () => {
            mongoAggregateMockReturn = [null, null];
            const res = await request(app).post(endpoint).send({
                chains: ['test_chain'], severities: [],
                sources: ['test_source'], minTimestamp: 0,
                maxTimestamp: 5000000000, noOfAlerts: 100
            });
            expect(res.statusCode).toEqual(536);
            expect(res.body)
                .toEqual({
                    error: 'Error: Could not retrieve data from Mongo.'
                });
        });
});

describe('Mongo Metrics POST Route', () => {
    const endpoint = '/server/mongo/metrics';

    it.each([
        ['no chains or systems are specified',
            {
                chains: [], systems: [], minTimestamp: 0,
                maxTimestamp: 5000000000, noOfMetricsPerSource: 100
            },
            [],
            {result: {metrics: {}}}],
        ['a single chain and a single system that has no metrics are specified',
            {
                chains: ['test_chain'], systems: ['test_system'],
                minTimestamp: 0, maxTimestamp: 5000000000,
                noOfMetricsPerSource: 100
            },
            [],
            {result: {metrics: {test_system: []}}}],
        ['a single chain and a single system that has some ' +
        'metrics are specified',
            {
                chains: ['test_chain'], systems: ['test_system'],
                minTimestamp: 0, maxTimestamp: 5000000000,
                noOfMetricsPerSource: 100
            },
            metricsSingleSystemMongoRet,
            metricsSingleSystemEndpointRet],
        ['multiple chains and multiple systems that have some ' +
        'metrics are specified',
            {
                chains: ['test_chain', 'test_chain2'],
                systems: ['test_system', 'test_system2'], minTimestamp: 0,
                maxTimestamp: 5000000000, noOfMetricsPerSource: 100
            },
            metricsMultipleSystemsMongoRet,
            metricsMultipleSystemsEndpointRet],
    ])('Should return correct result and a successful status code if %s',
        async (_: string, body: any, mongoRet: any[], endpointRet: any) => {
            mongoAggregateMockReturn = mongoRet;
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual(endpointRet);
        });

    it.each([
        [532,
            'chains, systems, minTimestamp, maxTimestamp, and ' +
            'noOfMetricsPerSource not specified',
            {},
            {
                error: 'Error: Missing key(s) chains, systems, minTimestamp, ' +
                    'maxTimestamp, noOfMetricsPerSource in body.'
            }],
        [532, 'chains not specified',
            {
                systems: [], minTimestamp: 0, maxTimestamp: 0,
                noOfMetricsPerSource: 1
            },
            {error: 'Error: Missing key(s) chains in body.'}],
        [532, 'systems not specified',
            {
                chains: [], minTimestamp: 0, maxTimestamp: 0,
                noOfMetricsPerSource: 1
            },
            {error: 'Error: Missing key(s) systems in body.'}],
        [532, 'minTimestamp not specified',
            {chains: [], systems: [], maxTimestamp: 0, noOfMetricsPerSource: 1},
            {error: 'Error: Missing key(s) minTimestamp in body.'}],
        [532, 'maxTimestamp not specified',
            {chains: [], systems: [], minTimestamp: 0, noOfMetricsPerSource: 1},
            {error: 'Error: Missing key(s) maxTimestamp in body.'}],
        [532, 'noOfMetricsPerSource not specified',
            {chains: [], systems: [], minTimestamp: 0, maxTimestamp: 0},
            {error: 'Error: Missing key(s) noOfMetricsPerSource in body.'}],
        [539, 'invalid chain specified (non-string)',
            {
                chains: ['test_chain', 123], systems: [], minTimestamp: 0,
                maxTimestamp: 0, noOfMetricsPerSource: 1
            },
            {error: 'Error: An invalid value was given to req.body.chains.'}],
        [539, 'invalid system specified (non-string)',
            {
                chains: [], systems: ['test_chain', 123], minTimestamp: 0,
                maxTimestamp: 0, noOfMetricsPerSource: 1
            },
            {error: 'Error: An invalid value was given to req.body.systems.'}],
        [539, 'invalid minTimestamp specified (string)',
            {
                chains: [], systems: [], minTimestamp: 'TEST', maxTimestamp: 0,
                noOfMetricsPerSource: 1
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.minTimestamp.'
            }],
        [539, 'invalid maxTimestamp specified (string)',
            {
                chains: [], systems: [], minTimestamp: 0, maxTimestamp: 'TEST',
                noOfMetricsPerSource: 1
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.maxTimestamp.'
            }],
        [539, 'invalid noOfMetricsPerSource specified (string)',
            {
                chains: [], systems: [], minTimestamp: 0, maxTimestamp: 0,
                noOfMetricsPerSource: 'TEST'
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.noOfMetricsPerSource.'
            }],
        [539, 'invalid minTimestamp specified (negative number)',
            {
                chains: [], systems: [], minTimestamp: -123, maxTimestamp: 0,
                noOfMetricsPerSource: 1
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.minTimestamp.'
            }],
        [539, 'invalid maxTimestamp specified (negative number)',
            {
                chains: [], systems: [], minTimestamp: 0, maxTimestamp: -123,
                noOfMetricsPerSource: 1
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.maxTimestamp.'
            }],
        [539, 'invalid noOfMetricsPerSource specified (negative number)',
            {
                chains: [], systems: [], minTimestamp: 0, maxTimestamp: 0,
                noOfMetricsPerSource: -123
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.noOfMetricsPerSource.'
            }],
        [539, 'invalid noOfMetricsPerSource specified (zero)',
            {
                chains: [], systems: [], minTimestamp: 0, maxTimestamp: 0,
                noOfMetricsPerSource: 0
            },
            {
                error: 'Error: An invalid value was given to ' +
                    'req.body.noOfMetricsPerSource.'
            }],
    ])('Should return error and %s status code if %s',
        async (statusCode: number, _: string, body: any,
               endpointRet: any) => {
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(statusCode);
            expect(res.body).toEqual(endpointRet);
        });
});

describe('Redis Alerts Overview POST Route', () => {
    const endpoint = '/server/redis/alertsOverview';

    it.each([
        ['a single chain with no sources is specified',
            {
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: [], nodes: [],
                        github_repos: [], dockerhub_repos: []
                    }
                }
            },
            {},
            {
                result: {
                    unique_chain_id: {
                        info: 0, critical: 0, warning: 0, error: 0,
                        problems: {}, releases: {}, tags: {}
                    }
                }
            }],
        ['a single chain with a single system that has no alerts is specified',
            {
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: ['test_system'], nodes: [],
                        github_repos: [], dockerhub_repos: []
                    }
                }
            },
            {},
            {
                result: {
                    unique_chain_id: {
                        info: 7, critical: 0, warning: 0, error: 0,
                        problems: {}, releases: {}, tags: {}
                    }
                }
            }],
        ['a single chain with a single node that has no alerts is specified',
            {
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: [], nodes: ['test_node'],
                        github_repos: [], dockerhub_repos: []
                    }
                }
            },
            {},
            {
                result: {
                    unique_chain_id: {
                        info: 52, critical: 0, warning: 0, error: 0,
                        problems: {}, releases: {}, tags: {}
                    }
                }
            }],
        ['a single chain with a single github repo that has no alerts is' +
        ' specified',
            {
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: [], nodes: [],
                        github_repos: ['test_repo'], dockerhub_repos: []
                    }
                }
            },
            {},
            {
                result: {
                    unique_chain_id: {
                        info: 3, critical: 0, warning: 0, error: 0,
                        problems: {}, releases: {}, tags: {}
                    }
                }
            }],
        ['a single chain with a single dockerhub repo that has no alerts is' +
        ' specified',
            {
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: [], nodes: [],
                        github_repos: [], dockerhub_repos: ['test_repo']
                    }
                }
            },
            {},
            {
                result: {
                    unique_chain_id: {
                        info: 5, critical: 0, warning: 0, error: 0,
                        problems: {}, releases: {}, tags: {}
                    }
                }
            }],
        ['a single chain with a single system that has some alerts is ' +
        'specified',
            {
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: ['test_system'], nodes: [],
                        github_repos: [], dockerhub_repos: []
                    }
                }
            },
            alertsOverviewSingleSystemRedisRet,
            alertsOverviewSingleSystemEndpointRet],
        ['a single chain with a single node that has some alerts is specified',
            {
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: [], nodes: ['test_node'],
                        github_repos: [], dockerhub_repos: []
                    }
                }
            },
            alertsOverviewSingleNodeRedisRet,
            alertsOverviewSingleNodeEndpointRet],
        ['a single chain with a single github repo that has some releases is' +
        ' specified',
            {
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: [], nodes: [],
                        github_repos: ['test_repo'], dockerhub_repos: []
                    }
                }
            },
            alertsOverviewSingleGitHubRepoRedisRet,
            alertsOverviewSingleGitHubRepoEndpointRet],
        ['a single chain with a single dockerhub repo that has some tag' +
        ' changes is specified',
            {
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: [], nodes: [],
                        github_repos: [], dockerhub_repos: ['test_repo']
                    }
                }
            },
            alertsOverviewSingleDockerHubRepoRedisRet,
            alertsOverviewSingleDockerHubRepoEndpointRet],
        ['a single chain which includes chain sourced alerts and chain has' +
        ' some alerts is specified',
            {
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: [], nodes: [],
                        github_repos: [], dockerhub_repos: []
                    }
                }
            },
            alertsOverviewChainSourceRedisRet,
            alertsOverviewChainSourceEndpointRet],
        ['a single chain which includes chain sourced alerts with unique identifier ' +
        'and chain has some alerts is specified',
            {
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: [], nodes: [],
                        github_repos: [], dockerhub_repos: []
                    }
                }
            },
            alertsOverviewChainSourceWithUniqueIdentifierRedisRet,
            alertsOverviewChainSourceWithUniqueIdentifierEndpointRet],
        ['a single chain with multiple sources that have alerts',
            {
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: ['test_system'],
                        nodes: ['test_node', 'test_evm_node'],
                        github_repos: ['test_github_repo'],
                        dockerhub_repos: ['test_dockerhub_repo']
                    }
                }
            },
            alertsOverviewMultipleSourcesRedisRet,
            alertsOverviewMultipleSourcesEndpointRet],
    ])('Should return correct result and a successful status code if %s',
        async (_: string, body: any, redisRet: { [p: string]: string },
               endpointRet: any) => {
            hgetallMockCallbackReply = redisRet;
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual(endpointRet);
        });

    it.each([
        [532, 'parentIds not specified', {},
            {error: 'Error: Missing key(s) parentIds in body.'}],
        [538, 'include_chain_sourced_alerts property not specified',
            {
                parentIds: {
                    systems: ['test_system'],
                    nodes: ['test_node'],
                    github_repos: ['test_github_repo'],
                    dockerhub_repos: ['test_dockerhub_repo']
                }
            },
            {error: parentIdsInvalidSchemaError}],
        [538, 'invalid properties are specified',
            {parentIds: {unique_chain_id: {test: []}}},
            {error: parentIdsInvalidSchemaError}],
    ])('Should return error and %s status code if %s',
        async (statusCode: number, _: string, body: any,
               endpointRet: any) => {
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(statusCode);
            expect(res.body).toEqual(endpointRet);
        });

    it('Should return error and status code 534 if redis returns ' +
        'an error',
        async () => {
            execMockCallbackError = new RedisError('Test Error');
            const res = await request(app).post(endpoint)
                .send({
                    parentIds: {
                        unique_chain_id: {
                            include_chain_sourced_alerts: true,
                            systems: [], nodes: [],
                            github_repos: [], dockerhub_repos: []
                        }
                    }
                });
            expect(res.statusCode).toEqual(534);
            expect(res.body)
                .toEqual({
                    error: 'Error: RedisError retrieved from Redis: Test Error.'
                });
        });

    it.each([
        ['a number', '123', '123'],
        ['a string (not null string)', 'test', 'test'],
        ['an invalid JSON', '{"test": "test"}', '[object Object]'],
    ])('Should return error and 540 status code if redis returns %s',
        async (_: string, invalidValue: string,
               invalidValueError: string) => {
            hgetallMockCallbackReply = {'alert_github1_test_repo': invalidValue}
            const res = await request(app).post(endpoint).send({
                parentIds: {
                    unique_chain_id: {
                        include_chain_sourced_alerts: true,
                        systems: [], nodes: [],
                        github_repos: ['test_repo'], dockerhub_repos: []
                    }
                }
            });
            expect(res.statusCode).toEqual(540);
            expect(res.body).toEqual({
                error: 'Error: Invalid value retrieved ' +
                    'from Redis: ' + invalidValueError + '.'
            });
        });
});

describe('Redis Metrics POST Route', () => {
    const endpoint = '/server/redis/metrics';

    it.each([
        ['a single chain with no sources is specified',
            {parentIds: {unique_chain_id: {systems: [], repos: []}}},
            [],
            {result: {unique_chain_id: {system: {}, github: {}}}}],
        ['a single chain with a single system that has no metrics is specified',
            {
                parentIds: {
                    unique_chain_id: {
                        systems: ['test_system'], repos: []
                    }
                }
            },
            noMetricsSingleSystemRedisRet,
            noMetricsSingleSystemRedisEndpointRet],
        ['a single chain with a single repo that has no metrics is specified',
            {parentIds: {unique_chain_id: {systems: [], repos: ['test_repo']}}},
            noMetricsSingleRepoRedisRet,
            noMetricsSingleRepoRedisEndpointRet],
        ['a single chain with a single system that has some metrics is ' +
        'specified',
            {
                parentIds: {
                    unique_chain_id: {
                        systems: ['test_system'], repos: []
                    }
                }
            },
            metricsSingleSystemRedisRet,
            metricsSingleSystemRedisEndpointRet],
        ['a single chain with a single repo that has some metrics is specified',
            {parentIds: {unique_chain_id: {systems: [], repos: ['test_repo']}}},
            metricsSingleRepoRedisRet,
            metricsSingleRepoRedisEndpointRet],
    ])('Should return correct result and a successful status code if %s',
        async (_: string, body: any, redisRet: string[],
               endpointRet: any) => {
            hmgetMockCallbackReply = redisRet;
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual(endpointRet);
        });

    it.each([
        [532, 'parentIds not specified', {},
            {error: 'Error: Missing key(s) parentIds in body.'}],
        [538, 'invalid properties are specified',
            {parentIds: {unique_chain_id: {test: []}}},
            {error: parentIdsInvalidSchemaError}],
    ])('Should return error and %s status code if %s',
        async (statusCode: number, _: string, body: any,
               endpointRet: any) => {
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(statusCode);
            expect(res.body).toEqual(endpointRet);
        });

    it('Should return error and status code 534 if redis returns ' +
        'an error',
        async () => {
            execMockCallbackError = new RedisError('Test Error');
            const res = await request(app).post(endpoint)
                .send({
                    parentIds:
                        {unique_chain_id: {systems: [], repos: []}}
                });
            expect(res.statusCode).toEqual(534);
            expect(res.body)
                .toEqual({
                    error: 'Error: RedisError retrieved from Redis: Test Error.'
                });
        });

    // For this endpoint, these redis returns do not cause an error since the
    // values are first passed to the JSON.stringify function.
    it.each([
        ['a number', '123'],
        ['a string (not null string)', 'test'],
        ['an invalid JSON', '{"test": "test"'],
    ])('Should return 200 status code if redis returns %s',
        async (_: string, invalidValue: string) => {
            hmgetMockCallbackReply = [invalidValue, 'null'];
            const res = await request(app).post(endpoint).send({
                parentIds:
                    {unique_chain_id: {systems: [], repos: []}}
            });
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({
                result: {
                    unique_chain_id: {
                        github: {},
                        system: {}
                    }
                }
            });
        });
});

describe('Ping Common Service - Node Exporter POST Route', () => {
    const endpoint = '/server/common/node-exporter';

    it('Should return error and status code if missing url in body', async () => {
        let expectedReturn = new MissingKeysInBody('url');
        const res = await request(app).post(endpoint).send({});
        expect(res.statusCode).toEqual(532);
        expect(res.body).toEqual({error: expectedReturn.message});
    });

    it('Should return correct result and a successful status code if node exporter does not return an error',
        async () => {
            const resp: AxiosResponse = emptyAxiosResponse('node_cpu_seconds_total');
            axiosMock.get.mockResolvedValue(resp);
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({result: PingStatus.SUCCESS});
        });

    it('Should return ping error and status code 400 if node exporter returns an error',
        async () => {
            axiosMock.get.mockResolvedValue(emptyAxiosResponse());
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({result: PingStatus.ERROR});
        });

    it('Should return ping timeout and status code 408 if node exporter returns a time out error',
        async () => {
            axiosMock.get.mockRejectedValue({code: 'ECONNABORTED'})
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(408);
            expect(res.body).toEqual({result: PingStatus.TIMEOUT});
        });
});

describe('Ping Common Service - Prometheus POST Route', () => {
    const endpoint = '/server/common/prometheus';

    it.each([
        [532, 'url not specified', {'baseChain': 'test'},
            {error: 'Error: Missing key(s) url in body.'}],
        [532, 'baseChain not specified', {'url': 'test'},
            {error: 'Error: Missing key(s) baseChain in body.'}],
        [532, 'url and baseChain not specified', {},
            {error: 'Error: Missing key(s) url, baseChain in body.'}],
    ])('Should return error and %s status code if %s',
        async (statusCode: number, _: string, body: any,
               endpointRet: any) => {
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(statusCode);
            expect(res.body).toEqual(endpointRet);
        });

    it.each([
        ['cosmos'],
        ['chainlink'],
        ['test chain'],
    ])('Should return correct result and a successful status code if prometheus does not return an error for % baseChain',
        async (baseChain: string) => {
            const resp: AxiosResponse = emptyAxiosResponse(getPrometheusMetricFromBaseChain(baseChain));
            axiosMock.get.mockResolvedValue(resp);
            const res = await request(app).post(endpoint).send({
                'url': 'test_url.com',
                'baseChain': baseChain
            });
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({result: PingStatus.SUCCESS});
        });

    it('Should return ping error and status code 400 if prometheus returns an error',
        async () => {
            axiosMock.get.mockResolvedValue(emptyAxiosResponse());
            const res = await request(app).post(endpoint).send({'url': 'test_url.com', 'baseChain': 'cosmos'});
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({result: PingStatus.ERROR});
        });

    it('Should return ping timeout and status code 408 if prometheus returns a time out error',
        async () => {
            axiosMock.get.mockRejectedValue({code: 'ECONNABORTED'})
            const res = await request(app).post(endpoint).send({'url': 'test_url.com', 'baseChain': 'cosmos'});
            expect(res.statusCode).toEqual(408);
            expect(res.body).toEqual({result: PingStatus.TIMEOUT});
        });
});

describe('Ping Cosmos Service - Cosmos REST POST Route', () => {
    const endpoint = '/server/cosmos/rest';

    it('Should return error and status code if missing url in body', async () => {
        let expectedReturn = new MissingKeysInBody('url');
        const res = await request(app).post(endpoint).send({});
        expect(res.statusCode).toEqual(532);
        expect(res.body).toEqual({error: expectedReturn.message});
    });

    it('Should return correct result and a successful status code if cosmos rest does not return an error',
        async () => {
            const resp: AxiosResponse = emptyAxiosResponse({node_info: 'test'});
            axiosMock.get.mockResolvedValue(resp);
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({result: PingStatus.SUCCESS});
        });

    it('Should return ping error and status code 400 if cosmos rest returns an error',
        async () => {
            axiosMock.get.mockResolvedValue(emptyAxiosResponse());
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({result: PingStatus.ERROR});
        });

    it('Should return ping timeout and status code 408 if cosmos rest returns a time out error',
        async () => {
            axiosMock.get.mockRejectedValue({code: 'ECONNABORTED'})
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(408);
            expect(res.body).toEqual({result: PingStatus.TIMEOUT});
        });
});

describe('Ping Cosmos Service - Tendermint RPC POST Route', () => {
    const endpoint = '/server/cosmos/tendermint-rpc';

    it('Should return error and status code if missing url in body', async () => {
        let expectedReturn = new MissingKeysInBody('url');
        const res = await request(app).post(endpoint).send({});
        expect(res.statusCode).toEqual(532);
        expect(res.body).toEqual({error: expectedReturn.message});
    });

    it('Should return correct result and a successful status code if tendermint rpc does not return an error',
        async () => {
            const resp: AxiosResponse = emptyAxiosResponse({jsonrpc: 'test'});
            axiosMock.get.mockResolvedValue(resp);
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({result: PingStatus.SUCCESS});
        });

    it('Should return ping error and status code 400 if tendermint rpc returns an error',
        async () => {
            axiosMock.get.mockResolvedValue(emptyAxiosResponse());
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({result: PingStatus.ERROR});
        });

    it('Should return ping timeout and status code 408 if tendermint rpc returns a time out error',
        async () => {
            axiosMock.get.mockRejectedValue({code: 'ECONNABORTED'})
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(408);
            expect(res.body).toEqual({result: PingStatus.TIMEOUT});
        });
});

describe('Ping Substrate Service - Websocket POST Route', () => {
    beforeEach(() => {
        process.env.SUBSTRATE_API_IP = '0.0.0.0';
        process.env.SUBSTRATE_API_PORT = '0000';
    });

    const endpoint = '/server/substrate/websocket';

    it('Should return error and status code if missing url in body',
        async () => {
            let expectedReturn = new MissingKeysInBody('url');
            const res = await request(app).post(endpoint).send({});
            expect(res.statusCode).toEqual(532);
            expect(res.body).toEqual({error: expectedReturn.message});
        });

    it('Should return error if Substrate env variables are not available',
        async () => {
            delete process.env.SUBSTRATE_API_IP;
            delete process.env.SUBSTRATE_API_PORT;
            const expectedReturn = new EnvVariablesNotAvailable('Substrate IP or Substrate API');
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(expectedReturn.code);
            expect(res.body).toEqual({error: expectedReturn.message});
        });

    it('Should return correct result and a successful status code if request does not return an error',
        async () => {
            axiosMock.get.mockResolvedValue(emptyAxiosResponse());
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({result: PingStatus.SUCCESS});
        });

    it('Should return ping error and status code 400 if request returns an error',
        async () => {
            axiosMock.get.mockRejectedValue({code: 'RANDOMERROR'})
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({result: PingStatus.ERROR});
        });

    it('Should return ping timeout and status code 408 if request times out',
        async () => {
            axiosMock.get.mockRejectedValue({code: 'ECONNABORTED'})
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(408);
            expect(res.body).toEqual({result: PingStatus.TIMEOUT});
        });
});

describe('Ping Ethereum Service - RPC POST Route', () => {
    const endpoint = '/server/ethereum/rpc';

    it('Should return error and status code if missing url in body', async () => {
        let expectedReturn = new MissingKeysInBody('url');
        const res = await request(app).post(endpoint).send({});
        expect(res.statusCode).toEqual(532);
        expect(res.body).toEqual({error: expectedReturn.message});
    });

    it('Should return correct result and a successful status code if web3 call does not return an error',
        async () => {
            web3EthGetBlockNumberPromiseResolve = 123;
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({result: PingStatus.SUCCESS});
        });

    it('Should return ping error and status code 400 if web3 call returns an error',
        async () => {
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({result: PingStatus.ERROR});
        });

    it('Should return ping timeout and status code 408 if web3 call times out',
        async () => {
            // While the web3 eth call will not return -1 in case of a timeout, this will mock the behaviour of the
            // fulfillWithTimeLimit function, which will return the failure value (-1) if the call times out. The
            // behaviour of this function is assumed to be valid and is tested in its respective unit tests.
            web3EthGetBlockNumberPromiseResolve = -1;
            const res = await request(app).post(endpoint).send({'url': 'test_url.com'});
            expect(res.statusCode).toEqual(408);
            expect(res.body).toEqual({result: PingStatus.TIMEOUT});
        });
});

describe('Send Test Alert Channels Opsgenie POST Route', () => {
    const endpoint = '/server/channels/opsgenie';

    it('Should return correct result and a successful status code if opsgenie does not return an error',
        async () => {
            const res = await request(app).post(endpoint)
                .send({'eu': true, 'apiKey': 'test'});
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({
                result: PingStatus.SUCCESS
            });
        });

    it.each([
        [532, 'apiKey not specified', {'eu': true},
            {error: 'Error: Missing key(s) apiKey in body.'}],
        [532, 'eu not specified', {'apiKey': 'test'},
            {error: 'Error: Missing key(s) eu in body.'}],
        [532, 'apiKey and eu not specified', {},
            {error: 'Error: Missing key(s) apiKey, eu in body.'}],
    ])('Should return error and %s status code if %s',
        async (statusCode: number, _: string, body: any,
               endpointRet: any) => {
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(statusCode);
            expect(res.body).toEqual(endpointRet);
        });

    it('Should return ping error and status code 400 if opsgenie returns an error',
        async () => {
            alertV2CreateMockCallbackError = Error();
            const res = await request(app).post(endpoint)
                .send({'eu': true, 'apiKey': 'test'});
            expect(res.statusCode).toEqual(400);
            expect(res.body)
                .toEqual({
                    result: PingStatus.ERROR
                });
        });
});

describe('Send Test Alert Channels PagerDuty POST Route', () => {
    const endpoint = '/server/channels/pagerduty';

    it('Should return correct result and a successful status code if pagerduty does not return an error',
        async () => {
            // @ts-ignore
            jest.spyOn(pagerDutyApi, 'event').mockResolvedValue('result');
            const res = await request(app).post(endpoint).send({'integrationKey': 'test'});
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({
                result: PingStatus.SUCCESS
            });
        });

    it('Should return error and %s status code if %s',
        async () => {
            const res = await request(app).post(endpoint).send({});
            expect(res.statusCode).toEqual(532);
            expect(res.body).toEqual({error: 'Error: Missing key(s) integrationKey in body.'});
        });

    it('Should return ping error and status code 400 if pagerduty returns an error',
        async () => {
            jest.spyOn(pagerDutyApi, 'event').mockRejectedValue('error');
            const res = await request(app).post(endpoint).send({'integrationKey': 'test'});
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({
                result: PingStatus.ERROR
            });
        });
});

describe('Send Test Alert Channels Slack POST Route', () => {
    const endpoint = '/server/channels/slack';

    it('Should return correct result and a successful status code if slack does not raise an error',
        async () => {
            const res = await request(app).post(endpoint)
                .send({'botToken': 'test', 'botChannelId': 'test'});
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({
                result: PingStatus.SUCCESS
            });
        });

    it.each([
        [532, 'botToken not specified', {'botChannelId': 'test'},
            {error: 'Error: Missing key(s) botToken in body.'}],
        [532, 'botChannelId not specified', {'botToken': 'test'},
            {error: 'Error: Missing key(s) botChannelId in body.'}],
        [532, 'botToken and botChannelId not specified', {},
            {error: 'Error: Missing key(s) botToken, botChannelId in body.'}],
    ])('Should return error and %s status code if %s',
        async (statusCode: number, _: string, body: any,
               endpointRet: any) => {
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(statusCode);
            expect(res.body).toEqual(endpointRet);
        });

    it('Should return ping error and status code 400 if slack raises an error',
        async () => {
            slackMock.chat.postMessage.mockImplementation(() => {
                throw new Error();
            });
            const res = await request(app).post(endpoint)
                .send({'botToken': 'test', 'botChannelId': 'test'});
            expect(res.statusCode).toEqual(400);
            expect(res.body)
                .toEqual({
                    result: PingStatus.ERROR
                });
        });
});

describe('Send Test Alert Channels Telegram POST Route', () => {
    const endpoint = '/server/channels/telegram';

    it('Should return correct result and a successful status code if telegram does not return an error',
        async () => {
            axiosMock.get.mockResolvedValue(emptyAxiosResponse());
            const res = await request(app).post(endpoint).send({'botToken': 'test', 'botChatId': 'test'});
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({result: PingStatus.SUCCESS});
        });

    it.each([
        [532, 'botToken not specified', {'botChatId': 'test'},
            {error: 'Error: Missing key(s) botToken in body.'}],
        [532, 'botChatId not specified', {'botToken': 'test'},
            {error: 'Error: Missing key(s) botChatId in body.'}],
        [532, 'botToken and botChatId not specified', {},
            {error: 'Error: Missing key(s) botToken, botChatId in body.'}],
    ])('Should return error and %s status code if %s',
        async (statusCode: number, _: string, body: any,
               endpointRet: any) => {
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(statusCode);
            expect(res.body).toEqual(endpointRet);
        });

    it('Should return ping error and status code 408 if telegram returns a time out error',
        async () => {
            axiosMock.get.mockRejectedValue({code: 'ECONNABORTED'});
            const res = await request(app).post(endpoint).send({'botToken': 'test', 'botChatId': 'test'});
            expect(res.statusCode).toEqual(408);
            expect(res.body).toEqual({result: PingStatus.TIMEOUT});
        });

    it('Should return ping error and status code 400 if telegram returns an error',
        async () => {
            axiosMock.get.mockRejectedValue({code: 'RANDOMERROR'});
            const res = await request(app).post(endpoint).send({'botToken': 'test', 'botChatId': 'test'});
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({result: PingStatus.ERROR});
        });
});

describe('Send Test Alert Channels PagerDuty POST Route', () => {
    const endpoint = '/server/channels/pagerduty';

    it('Should return correct result and a successful status code if pagerduty does not return an error',
        async () => {
            // @ts-ignore
            jest.spyOn(pagerDutyApi, 'event').mockResolvedValue('result');
            const res = await request(app).post(endpoint).send({'integrationKey': 'test'});
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({
                result: PingStatus.SUCCESS
            });
        });

    it('Should return error and %s status code if %s',
        async () => {
            const res = await request(app).post(endpoint).send({});
            expect(res.statusCode).toEqual(532);
            expect(res.body).toEqual({error: 'Error: Missing key(s) integrationKey in body.'});
        });

    it('Should return ping error and status code 400 if pagerduty returns an error',
        async () => {
            jest.spyOn(pagerDutyApi, 'event').mockRejectedValue('error');
            const res = await request(app).post(endpoint).send({'integrationKey': 'test'});
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({
                result: PingStatus.ERROR
            });
        });
});

describe('Send Test Alert Channels Twilio POST Route', () => {
    const endpoint = '/server/channels/twilio';

    it('Should return correct result and a successful status code if twilio does not return an error',
        async () => {
            twilioClientCallsCreateResolve = {test: 'test'}
            const res = await request(app).post(endpoint).send({
                accountSid: 'test', authToken: 'test',
                twilioPhoneNumber: 'test', phoneNumberToDial: 'test'
            });
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({result: PingStatus.SUCCESS});
        });

    it.each([
        [532, 'accountSid not specified',
            {authToken: 'test', twilioPhoneNumber: 'test', phoneNumberToDial: 'test'},
            {error: 'Error: Missing key(s) accountSid in body.'}],
        [532, 'authToken not specified',
            {accountSid: 'test', twilioPhoneNumber: 'test', phoneNumberToDial: 'test'},
            {error: 'Error: Missing key(s) authToken in body.'}],
        [532, 'twilioPhoneNumber not specified',
            {accountSid: 'test', authToken: 'test', phoneNumberToDial: 'test'},
            {error: 'Error: Missing key(s) twilioPhoneNumber in body.'}],
        [532, 'phoneNumberToDial not specified',
            {accountSid: 'test', authToken: 'test', twilioPhoneNumber: 'test'},
            {error: 'Error: Missing key(s) phoneNumberToDial in body.'}],
        [532, 'accountSid and authToken not specified',
            {twilioPhoneNumber: 'test', phoneNumberToDial: 'test'},
            {error: 'Error: Missing key(s) accountSid, authToken in body.'}],
        [532, 'twilioPhoneNumber and phoneNumberToDial not specified',
            {accountSid: 'test', authToken: 'test'},
            {error: 'Error: Missing key(s) twilioPhoneNumber, phoneNumberToDial in body.'}],
        [532, 'accountSid, authToken, twilioPhoneNumber, and phoneNumberToDial not specified', {},
            {error: 'Error: Missing key(s) accountSid, authToken, twilioPhoneNumber, phoneNumberToDial in body.'}],
    ])('Should return error and %s status code if %s',
        async (statusCode: number, _: string, body: any,
               endpointRet: any) => {
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(statusCode);
            expect(res.body).toEqual(endpointRet);
        });

    it('Should return ping error and status code 400 if twilio returns an error',
        async () => {
            const res = await request(app).post(endpoint).send({
                accountSid: 'test', authToken: 'test',
                twilioPhoneNumber: 'test', phoneNumberToDial: 'test'
            });
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({result: PingStatus.ERROR});
        });
});

describe('Send Test Alert Channels Email POST Route', () => {
    const endpoint = '/server/channels/email';

    it('Should return correct result and a successful status code if email does not return an error',
        async () => {
            const res = await request(app).post(endpoint).send({
                smtp: 'test', port: 123, from: 'test', to: 'test',
                username: 'test', password: 'test'
            });
            expect(res.statusCode).toEqual(200);
            expect(res.body).toEqual({result: PingStatus.SUCCESS});
        });

    it.each([
        [532, 'smtp not specified',
            {port: 123, from: 'test', to: 'test', username: '', password: ''},
            {error: 'Error: Missing key(s) smtp in body.'}],
        [532, 'port not specified',
            {smtp: 'test', from: 'test', to: 'test', username: '', password: ''},
            {error: 'Error: Missing key(s) port in body.'}],
        [532, 'from not specified',
            {smtp: 'test', port: 123, to: 'test', username: '', password: ''},
            {error: 'Error: Missing key(s) from in body.'}],
        [532, 'to not specified',
            {smtp: 'test', port: 123, from: 'test', username: '', password: ''},
            {error: 'Error: Missing key(s) to in body.'}],
        [532, 'username not specified',
            {smtp: 'test', port: 123, from: 'test', to: 'test', password: ''},
            {error: 'Error: Missing key(s) username in body.'}],
        [532, 'password not specified',
            {smtp: 'test', port: 123, from: 'test', to: 'test', username: ''},
            {error: 'Error: Missing key(s) password in body.'}],
        [532, 'smtp and port not specified',
            {from: 'test', to: 'test', username: '', password: ''},
            {error: 'Error: Missing key(s) smtp, port in body.'}],
        [532, 'username and password not specified',
            {smtp: 'test', port: 123, from: 'test', to: 'test'},
            {error: 'Error: Missing key(s) username, password in body.'}],
        [532, 'smtp, port, from, to, username, and password not specified', {},
            {error: 'Error: Missing key(s) smtp, port, from, to, username, password in body.'}],
    ])('Should return error and %s status code if %s',
        async (statusCode: number, _: string, body: any,
               endpointRet: any) => {
            const res = await request(app).post(endpoint).send(body);
            expect(res.statusCode).toEqual(statusCode);
            expect(res.body).toEqual(endpointRet);
        });

    it('Should return ping error and status code 400 if email client returns an error',
        async () => {
            nodemailerVerifyCallbackError = Error();
            const res = await request(app).post(endpoint).send({
                smtp: 'test', port: 123, from: 'test', to: 'test',
                username: 'test', password: 'test'
            });
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({result: PingStatus.ERROR});
        });

    it('Should return ping error and status code 400 if sending email returns an error',
        async () => {
            nodemailerSendMailCallbackError = Error();
            const res = await request(app).post(endpoint).send({
                smtp: 'test', port: 123, from: 'test', to: 'test',
                username: 'test', password: 'test'
            });
            expect(res.statusCode).toEqual(400);
            expect(res.body).toEqual({result: PingStatus.ERROR});
        });
});

describe('Server Defaults', () => {
    it.each([
        ['/server/'], ['/server/bad-endpoint']
    ])('Should return status code 531 and an error if GET request %s',
        async (endpoint: string) => {
            let expectedReturn = new InvalidEndpoint(endpoint);
            const res = await request(app).get(endpoint);
            expect(res.statusCode).toEqual(expectedReturn.code);
            expect(res.body).toEqual({
                'error': expectedReturn.message
            });
        });

    it.each([
        ['/server/'], ['/server/bad-endpoint']
    ])('Should return status code 531 and an error if POST request %s',
        async (endpoint: string) => {
            let expectedReturn = new InvalidEndpoint(endpoint);
            const res = await request(app).post(endpoint);
            expect(res.statusCode).toEqual(expectedReturn.code);
            expect(res.body).toEqual({
                'error': expectedReturn.message
            });
        });
});

describe('Server Redirects', () => {
    const expectedReturnedText: string = 'Found. Redirecting to /api-docs';
    const expectedStatusCode: number = 302;
    it.each([
        ['/'], ['/bad-endpoint']
    ])('Should return status code 302 and an error if GET request %s',
        async (endpoint: string) => {
            const res = await request(app).get(endpoint);
            expect(res.statusCode).toEqual(expectedStatusCode);
            expect(res.text).toEqual(expectedReturnedText);
        });

    it.each([
        ['/'], ['/bad-endpoint']
    ])('Should return status code 302 and an error if POST request %s',
        async (endpoint: string) => {
            const res = await request(app).post(endpoint);
            expect(res.statusCode).toEqual(expectedStatusCode);
            expect(res.text).toEqual(expectedReturnedText);
        });
});
