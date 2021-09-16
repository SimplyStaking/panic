import { ChainsAPI } from "../chains";
import { baseChainsNames } from "../constants";

beforeEach(() => {
    fetch.resetMocks();
});

describe('getBaseChains() function', () => {
    it('should not return any base chains when API is down', async () => {
        fetch.mockReject(() => Promise.reject("API is down"));
        const baseChains = await ChainsAPI.updateBaseChains([{
            name: '', chains: [
                {
                    name: '', id: '', repos: [], systems: [], criticalAlerts: 0,
                    warningAlerts: 0, errorAlerts: 0, totalAlerts: 0, active: false
                }]
        }]);

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    const mockBaseChainsData = [{
        name: 'cosmos', chains: [
            {
                name: 'test chain', id: 'test_chain', repos: ['test_repo'],
                systems: ['test_system'], criticalAlerts: 0, warningAlerts: 0,
                errorAlerts: 0, totalAlerts: 0, active: true
            }]
    }];

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

    it('should not update chain when getAlertsOverview fails', async () => {
        fetch.mockResponseOnce(JSON.stringify(monitorablesInfoMockData))
            .mockReject(() => Promise.reject("API is down"));

        const baseChains = await ChainsAPI.updateBaseChains(mockBaseChainsData);

        expect(baseChains).toEqual(mockBaseChainsData);
        expect(fetch).toHaveBeenCalledTimes(2);
    });

    it('should not change base chains if alerts did not change', async () => {
        const alertsOverviewMockData = {
            result: { test_chain: { critical: 0, warning: 0, error: 0 } }
        };

        fetch.mockResponses([JSON.stringify(monitorablesInfoMockData)],
            [JSON.stringify(alertsOverviewMockData)]);

        const baseChains = await ChainsAPI.updateBaseChains(mockBaseChainsData);

        expect(baseChains).toEqual(mockBaseChainsData);
        expect(fetch).toHaveBeenCalledTimes(2);
    });

    it('should update base chains if alerts changed', async () => {
        const alertsOverviewMockData2 = {
            result: { test_chain: { critical: 1, warning: 3, error: 2 } }
        };

        const mockBaseChainsData2 = [...mockBaseChainsData];
        mockBaseChainsData2[0].chains[0].errorAlerts = 2;
        mockBaseChainsData2[0].chains[0].totalAlerts = 6;

        fetch.mockResponses([JSON.stringify(monitorablesInfoMockData)],
            [JSON.stringify(alertsOverviewMockData2)]);

        const baseChains = await ChainsAPI.updateBaseChains(mockBaseChainsData);

        expect(baseChains).toEqual(mockBaseChainsData2);
        expect(fetch).toHaveBeenCalledTimes(2);
    });
});
