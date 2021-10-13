import { SeverityAPI } from "../severity";
import { ChainsAPI } from "../chains";
import { baseChainsNames, fetchMock } from "../constants";

beforeEach(() => {
    fetchMock.resetMocks();
});

describe('getBaseChains() function', () => {
    it('should not return any base chains when API is down', async () => {
        fetchMock.mockReject(() => Promise.reject("API is down"));
        const baseChains = await ChainsAPI.updateBaseChains([{
            name: '',
            activeSeverities: SeverityAPI.getAllSeverityValues(true),
            lastClickedColumnIndex: 1,
            ordering: 'descending',
            chains: [
                {
                    name: 'test chain', id: 'test', repos: [],
                    systems: [], alerts: [], active: true
                }]
        }]);

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    const mockBaseChainsData = [{
        name: 'cosmos',
        activeSeverities: SeverityAPI.getAllSeverityValues(true),
        lastClickedColumnIndex: 1,
        ordering: 'descending',
        chains: [
            {
                name: 'test chain', id: 'test_chain', repos: ['test_repo'],
                systems: ['test_system'], alerts: [], active: true
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
        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfoMockData))
            .mockReject(() => Promise.reject("API is down"));

        const baseChains = await ChainsAPI.updateBaseChains(mockBaseChainsData);

        expect(baseChains).toEqual(mockBaseChainsData);
        expect(fetch).toHaveBeenCalledTimes(2);
    });

    it('should not change base chains if alerts did not change', async () => {
        const alertsOverviewMockData = {
            result: { test_chain: { critical: 0, warning: 0, error: 0 } }
        };

        fetchMock.mockResponses([JSON.stringify(monitorablesInfoMockData)],
            [JSON.stringify(alertsOverviewMockData)]);

        const baseChains = await ChainsAPI.updateBaseChains(mockBaseChainsData);

        expect(baseChains).toEqual(mockBaseChainsData);
        expect(fetch).toHaveBeenCalledTimes(2);
    });

    it('should update base chains if alerts changed', async () => {
        const alertsOverviewMockData2 = {
            result: {
                test_chain: {
                    critical: 1, warning: 3, error: 2,
                    problems: {
                        test_chain: [{ severity: 'WARNING', message: 'test alert 1', timestamp: 12345 },
                        { severity: 'WARNING', message: 'test alert 2', timestamp: 12345 },
                        { severity: 'WARNING', message: 'test alert 3', timestamp: 12345 },
                        { severity: 'ERROR', message: 'test alert 4', timestamp: 12345 },
                        { severity: 'ERROR', message: 'test alert 5', timestamp: 12345 }]
                    }
                }
            }
        };

        const mockBaseChainsData2 = [...mockBaseChainsData];
        mockBaseChainsData2[0].chains[0].alerts.push(
            { severity: 'WARNING', message: 'test alert 1', timestamp: 12345 },
            { severity: 'WARNING', message: 'test alert 2', timestamp: 12345 },
            { severity: 'WARNING', message: 'test alert 3', timestamp: 12345 },
            { severity: 'ERROR', message: 'test alert 4', timestamp: 12345 },
            { severity: 'ERROR', message: 'test alert 5', timestamp: 12345 });

        fetchMock.mockResponses([JSON.stringify(monitorablesInfoMockData)],
            [JSON.stringify(alertsOverviewMockData2)]);

        const baseChains = await ChainsAPI.updateBaseChains(mockBaseChainsData);

        expect(baseChains).toEqual(mockBaseChainsData2);
        expect(fetch).toHaveBeenCalledTimes(2);
    });
});
