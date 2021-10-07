import { AlertsAPI } from "../alerts";
import { ChainsAPI } from "../chains";
import { baseChainsNames, fetchMock } from "../constants";

beforeEach(() => {
    fetchMock.resetMocks();
});

describe('getBaseChains() function', () => {
    it('should not return any base chains when API is down', async () => {
        fetchMock.mockReject(() => Promise.reject("API is down"));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should not return any base chains when there are no base chains', async () => {
        const monitorablesInfoNoBaseChains: any = { result: {} };
        for (const baseChainName of baseChainsNames) {
            monitorablesInfoNoBaseChains.result[baseChainName] = null;
        }

        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfoNoBaseChains));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should not return a base chain if it does not contain any chains', async () => {
        const monitorablesInfo1BaseChain0Chains: any = { result: {} };
        for (const baseChainName of baseChainsNames) {
            monitorablesInfo1BaseChain0Chains.result[baseChainName] = null;
        }
        monitorablesInfo1BaseChain0Chains.result[baseChainsNames[0]] = {};

        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfo1BaseChain0Chains));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should not return a base chain if all of its chains do not have the monitored field', async () => {
        const monitorablesInfoWithoutMonitored: any = { result: {} };
        for (const baseChainName of baseChainsNames) {
            monitorablesInfoWithoutMonitored.result[baseChainName] = null;
        }

        monitorablesInfoWithoutMonitored.result[baseChainsNames[0]] = { 'test chain': { parent_id: "test_chain" } };
        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfoWithoutMonitored));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should not return a base chain if no sources are available within its chains', async () => {
        const monitorablesInfoEmptyMonitored: any = { result: {} };
        for (const baseChainName of baseChainsNames) {
            monitorablesInfoEmptyMonitored.result[baseChainName] = null;
        }
        monitorablesInfoEmptyMonitored.result[baseChainsNames[0]] = { 'test chain': { parent_id: "test_chain", monitored: {} } };

        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfoEmptyMonitored));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should not return a base chain if no systems (and no repos) are available within its chains', async () => {
        const monitorablesInfoEmptySystems: any = { result: {} };
        for (const baseChainName of baseChainsNames) {
            monitorablesInfoEmptySystems.result[baseChainName] = null;
        }
        monitorablesInfoEmptySystems.result[baseChainsNames[0]] = { 'test chain': { parent_id: "test_chain", monitored: { systems: [] } } };

        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfoEmptySystems));
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

        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfoEmptyRepos));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should return the base chain when its chains contain valid sources', async () => {
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

        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfoMockData));
        const baseChains = await ChainsAPI.getBaseChains();

        expect(baseChains).toEqual([{
            name: 'cosmos', activeChains: ['test chain'],
            activeSeverities: AlertsAPI.getAllSeverityValues(),
            chains: [{
                id: "test_chain", name: 'test chain', repos: ['test_repo'],
                systems: ['test_system'], alerts: [], active: true
            }]
        }]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });
});
