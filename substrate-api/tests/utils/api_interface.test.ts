import {
    initialiseWsInterface,
    WsInterfacesManager
} from "../../src/utils/api_interface";
import {mocked} from "ts-jest/utils";
import {ApiPromise, WsProvider} from "@polkadot/api";
import {TestApiPromise, TestWsProvider} from "../test-utils";

let testWsUrl = 'testWsUrl';
let testWsProvider: TestWsProvider;
let testApiPromise: TestApiPromise;
let wsInterfacesManager: WsInterfacesManager;

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

// Create mocking variables for both ApiPromise and WsProvider so that we can
// can generate errors from their functions
const mockedWsProvider = mocked(WsProvider, true);
const mockedApiPromise = mocked(ApiPromise, true);

// This is used to clear all mock data after each test
beforeEach(() => {
    jest.clearAllMocks();
    testWsProvider = new TestWsProvider(testWsUrl);
    testApiPromise = new TestApiPromise(testWsUrl);
    wsInterfacesManager = new WsInterfacesManager();
});

describe('initialiseWsInterface', () => {
    it('should create and return provider and API instance if successful',
        async () => {
            let ret = await initialiseWsInterface(testWsUrl);
            expect(ret).toBeDefined();
            if (ret) {
                expect(ret.provider).toEqual(testWsProvider);
                expect(ret.api).toEqual(testApiPromise);
            } else {
                fail('Return from initialiseWsInterface should not have been ' +
                    'Falsy')
            }
        });
    it('should return nothing and not call provider.disconnect if provider ' +
        'init error',
        async () => {
            // Need to change the module mock's init implementation to throw
            // error
            mockedWsProvider.mockImplementationOnce(
                () => {
                    throw new Error('WsProvider error')
                }
            );

            // Mock the disconnect function to check if it was called.
            testWsProvider.disconnect = jest.fn();

            let ret = await initialiseWsInterface(testWsUrl);
            expect(ret).toBeUndefined();
            expect(testWsProvider.disconnect).toHaveBeenCalledTimes(0)
        });
    it('should return nothing and call provider.disconnect if API init error',
        async () => {
            // Need to change the module mock's create implementation to throw
            // error
            mockedApiPromise.create = jest.fn().mockImplementation(
                () => {
                    throw new Error('ApiPromise error')
                }
            );

            // Mock the disconnect function to check if it was called.
            testWsProvider.disconnect = jest.fn();

            let ret = await initialiseWsInterface(testWsUrl);
            expect(ret).toBeUndefined();
            expect(testWsProvider.disconnect).toHaveBeenCalledTimes(1);

            // Reset to previous mock to avoid issues with upcoming tests
            mockedApiPromise.create = jest.fn().mockImplementation(
                () => {
                    return testApiPromise
                }
            );
        })
});

describe('WsInterfacesManager', () => {
    it('createInterface returns false and initialises if no previous ' +
        'initialisation',
        async () => {
            let ret = await wsInterfacesManager.createInterface(testWsUrl);
            let expectedInterface = {
                api: testApiPromise,
                provider: testWsProvider
            };
            expect(ret).toEqual(false);
            expect(wsInterfacesManager.wsInterfaces[testWsUrl]).toEqual(
                expectedInterface
            )
        });
    it('createInterface returns false and does not initialise if ' +
        'already initialised',
        async () => {
            // Create an instance and check that the init functions were both
            // called
            await wsInterfacesManager.createInterface(testWsUrl);
            expect(mockedWsProvider).toHaveBeenCalledTimes(1);
            expect(mockedApiPromise.create).toHaveBeenCalledTimes(1);

            // Call again and check that the init functions were not called
            // again, and false was returned.
            let ret = await wsInterfacesManager.createInterface(testWsUrl);
            expect(mockedWsProvider).toHaveBeenCalledTimes(1);
            expect(mockedApiPromise.create).toHaveBeenCalledTimes(1);
            expect(ret).toEqual(false);
        });
    it('createInterface returns true and does not initialise if ' +
        'nothing returned from initialiser',
        async () => {
            // Need to change the module mock's create implementation to throw
            // error and return nothing from initialiseWsInterface
            mockedApiPromise.create = jest.fn().mockImplementation(
                () => {
                    throw new Error('ApiPromise error')
                }
            );

            let ret = await wsInterfacesManager.createInterface(testWsUrl);
            expect(ret).toEqual(true);
            expect(wsInterfacesManager.wsInterfaces).toEqual({});

            // Reset to previous mock to avoid issues with upcoming tests
            mockedApiPromise.create = jest.fn().mockImplementation(
                () => {
                    return testApiPromise
                }
            );
        });
    it('createInterface returns true and does not initialise if ' +
        'initialiser error',
        async () => {
            // Need to change the module mock's create implementation to throw
            // error and return nothing from initialiseWsInterface. We will also
            // generate an exception from provider.disconnect to test if
            // exceptions are caught.
            mockedApiPromise.create = jest.fn().mockImplementation(
                () => {
                    throw new Error('ApiPromise error')
                }
            );
            testWsProvider.disconnect = jest.fn().mockImplementation(
                () => {
                    throw new Error('provider.disconnect error')
                }
            );

            let ret = await wsInterfacesManager.createInterface(testWsUrl);
            expect(ret).toEqual(true);
            expect(wsInterfacesManager.wsInterfaces).toEqual({});

            // Reset to previous mock to avoid issues with upcoming tests
            mockedApiPromise.create = jest.fn().mockImplementation(
                () => {
                    return testApiPromise
                }
            );
        });
    it('removeInterface disconnects, removes interface and returns false ' +
        'if an initialisation exists',
        async () => {
            // Mock the disconnect function to check if it was called.
            testWsProvider.disconnect = jest.fn();

            // Create interface to be removed
            await wsInterfacesManager.createInterface(testWsUrl);

            let ret = await wsInterfacesManager.removeInterface(testWsUrl);
            expect(ret).toEqual(false);
            expect(testWsProvider.disconnect).toHaveBeenCalledTimes(1);
            expect(wsInterfacesManager.wsInterfaces).toEqual({});
        });
    it('removeInterface returns false and does nothing if no initialisation ' +
        'exists',
        async () => {
            // Mock the disconnect function to check if it was called.
            testWsProvider.disconnect = jest.fn();

            let ret = await wsInterfacesManager.removeInterface(testWsUrl);
            expect(ret).toEqual(false);
            expect(testWsProvider.disconnect).toHaveBeenCalledTimes(0);
        });
    it('removeInterface returns true and does not remove initialisation if ' +
        'disconnection error',
        async () => {
            // Mock the disconnect function to generate an error.
            testWsProvider.disconnect = jest.fn().mockImplementation(
                () => {
                    throw new Error('provider.disconnect error')
                }
            );

            // Create interface to be removed
            await wsInterfacesManager.createInterface(testWsUrl);

            let ret = await wsInterfacesManager.removeInterface(testWsUrl);

            let expectedInterface = {
                api: testApiPromise,
                provider: testWsProvider
            };
            expect(ret).toEqual(true);
            expect(wsInterfacesManager.wsInterfaces[testWsUrl]).toEqual(
                expectedInterface
            )
        });
});
