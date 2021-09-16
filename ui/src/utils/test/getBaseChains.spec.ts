import { ChainsAPI } from "../chains";
import { baseChainsNames } from "../constants";
import { enableFetchMocks } from 'jest-fetch-mock'
enableFetchMocks()

beforeEach(() => {
    fetch.resetMocks();
});

describe('getBaseChains() function', () => {
    it('should not return any base chains when API is down', async () => {
        fetch.mockReject(() => Promise.reject("API is down"));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    const monitorablesInfoNoBaseChains: any = { result: {} };
    for (const baseChainName of baseChainsNames) {
        monitorablesInfoNoBaseChains.result[baseChainName] = null;
    }

    it('should not return any base chains when there are no base chains', async () => {
        fetch.mockResponseOnce(JSON.stringify(monitorablesInfoNoBaseChains));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    const monitorablesInfo1BaseChain0Chains: any = { result: {} };
    for (const baseChainName of baseChainsNames) {
        monitorablesInfo1BaseChain0Chains.result[baseChainName] = null;
    }

    monitorablesInfo1BaseChain0Chains.result[baseChainsNames[0]] = {};

    it('should not return a base chain if it does not contain any chains', async () => {
        fetch.mockResponseOnce(JSON.stringify(monitorablesInfo1BaseChain0Chains));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    const monitorablesInfoWithoutMonitored: any = { result: {} };
    for (const baseChainName of baseChainsNames) {
        monitorablesInfoWithoutMonitored.result[baseChainName] = null;
    }

    monitorablesInfoWithoutMonitored.result[baseChainsNames[0]] = { 'test chain': { parent_id: "test_chain" } };

    it('should not return a base chain if all of its chains do not have the monitored field', async () => {
        fetch.mockResponseOnce(JSON.stringify(monitorablesInfoWithoutMonitored));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    const monitorablesInfoEmptyMonitored: any = { result: {} };
    for (const baseChainName of baseChainsNames) {
        monitorablesInfoEmptyMonitored.result[baseChainName] = null;
    }

    monitorablesInfoEmptyMonitored.result[baseChainsNames[0]] = { 'test chain': { parent_id: "test_chain", monitored: {} } };

    it('should not return a base chain if no sources are available within its chains', async () => {
        fetch.mockResponseOnce(JSON.stringify(monitorablesInfoWithoutMonitored));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    const monitorablesInfoEmptySystems: any = { result: {} };
    for (const baseChainName of baseChainsNames) {
        monitorablesInfoEmptySystems.result[baseChainName] = null;
    }

    monitorablesInfoEmptySystems.result[baseChainsNames[0]] = { 'test chain': { parent_id: "test_chain", monitored: { systems: [] } } };

    it('should not return a base chain if no systems (and no repos) are available within its chains', async () => {
        fetch.mockResponseOnce(JSON.stringify(monitorablesInfoEmptySystems));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should not return a base chain if no repos (and no systems) are available within its chains', async () => {
        const monitorablesInfoEmptyRepos: any = { result: {} };
        for (const baseChainName of baseChainsNames) {
            monitorablesInfoEmptyRepos.result[baseChainName] = null;
        }

        monitorablesInfoEmptyRepos.result[baseChainsNames[0]] = { 'test chain': { parent_id: "test_chain", monitored: { github_repos: [] } } };

        fetch.mockResponseOnce(JSON.stringify(monitorablesInfoEmptyRepos));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    const monitorablesInfoMockData: any = { result: {} };
    for (const baseChainName of baseChainsNames) {
        monitorablesInfoMockData.result[baseChainName] = null;
    }

    monitorablesInfoMockData.result[baseChainsNames[0]] = {
        'test chain': {
            parent_id: "test_chain", monitored: {
                systems: [{ 'test_system': 'test_system' }],
                github_repos: [{ 'test_repo': 'test_repo' }]
            }
        }
    };

    it('should return the base chain when its chains contain valid sources', async () => {
        fetch.mockResponseOnce(JSON.stringify(monitorablesInfoMockData));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([{
            name: 'cosmos', chains: [{
                id: "test_chain", name: 'test chain', repos: ['test_repo'],
                systems: ['test_system'], criticalAlerts: 0, warningAlerts: 0,
                errorAlerts: 0, totalAlerts: 0, active: true
            }]
        }]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });
});
