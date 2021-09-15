import { ChainsAPI } from "../chains";
import { baseChainsNames } from "../constants";

fetch = jest.fn(() =>
    Promise.reject("API is down"));

beforeEach(() => {
    fetch.mockClear();
});

it('getBaseChains() - API is down', async () => {
    const baseChains = await ChainsAPI.getBaseChains();

    expect(baseChains).toEqual([]);
    expect(fetch).toHaveBeenCalledTimes(1);
});

const monitorablesInfoNoBaseChains: any = { result: {} };
for (const baseChainName of baseChainsNames) {
    monitorablesInfoNoBaseChains.result[baseChainName] = null;
}

it('getBaseChains() - no base chains', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
        json: () => Promise.resolve(monitorablesInfoNoBaseChains),
    }));
    const baseChains = await ChainsAPI.getBaseChains();

    expect(baseChains).toEqual([]);
    expect(fetch).toHaveBeenCalledTimes(1);
});

const monitorablesInfo1BaseChain0Chains: any = { result: {} };
for (const baseChainName of baseChainsNames) {
    monitorablesInfo1BaseChain0Chains.result[baseChainName] = null;
}

monitorablesInfo1BaseChain0Chains.result[baseChainsNames[0]] = {};

it('getBaseChains() - 1 base chain 0 chains', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
        json: () => Promise.resolve(monitorablesInfo1BaseChain0Chains),
    }));
    const baseChains = await ChainsAPI.getBaseChains();

    expect(baseChains).toEqual([]);
    expect(fetch).toHaveBeenCalledTimes(1);
});

const monitorablesInfoWithoutMonitored: any = { result: {} };
for (const baseChainName of baseChainsNames) {
    monitorablesInfoWithoutMonitored.result[baseChainName] = null;
}

monitorablesInfoWithoutMonitored.result[baseChainsNames[0]] = { 'test chain': { parent_id: "test_chain" } };

it('getBaseChains() - chain without monitored field', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
        json: () => Promise.resolve(monitorablesInfoWithoutMonitored),
    }));
    const baseChains = await ChainsAPI.getBaseChains();

    expect(baseChains).toEqual([]);
    expect(fetch).toHaveBeenCalledTimes(1);
});

const monitorablesInfoEmptyMonitored: any = { result: {} };
for (const baseChainName of baseChainsNames) {
    monitorablesInfoEmptyMonitored.result[baseChainName] = null;
}

monitorablesInfoEmptyMonitored.result[baseChainsNames[0]] = { 'test chain': { parent_id: "test_chain", monitored: {} } };

it('getBaseChains() - chain with empty monitored field', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
        json: () => Promise.resolve(monitorablesInfoWithoutMonitored),
    }));
    const baseChains = await ChainsAPI.getBaseChains();

    expect(baseChains).toEqual([]);
    expect(fetch).toHaveBeenCalledTimes(1);
});

const monitorablesInfoEmptySystems: any = { result: {} };
for (const baseChainName of baseChainsNames) {
    monitorablesInfoEmptySystems.result[baseChainName] = null;
}

monitorablesInfoEmptySystems.result[baseChainsNames[0]] = { 'test chain': { parent_id: "test_chain", monitored: { systems: [] } } };

it('getBaseChains() - chain with empty systems field', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
        json: () => Promise.resolve(monitorablesInfoEmptySystems),
    }));
    const baseChains = await ChainsAPI.getBaseChains();

    expect(baseChains).toEqual([]);
    expect(fetch).toHaveBeenCalledTimes(1);
});

const monitorablesInfoEmptyRepos: any = { result: {} };
for (const baseChainName of baseChainsNames) {
    monitorablesInfoEmptyRepos.result[baseChainName] = null;
}

monitorablesInfoEmptyRepos.result[baseChainsNames[0]] = { 'test chain': { parent_id: "test_chain", monitored: { github_repos: [] } } };

it('getBaseChains() - chain with empty repos field', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
        json: () => Promise.resolve(monitorablesInfoEmptyRepos),
    }));
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

it('getBaseChains() - chain with mock data', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
        json: () => Promise.resolve(monitorablesInfoMockData),
    }));
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

it('updateBaseChains() - API is down', async () => {
    fetch.mockImplementationOnce(() => Promise.reject("API is down"));
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

it('updateBaseChains() - API is down during second call', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
        json: () => Promise.resolve(monitorablesInfoMockData),
    })).mockImplementationOnce(() => Promise.reject("API is down"));

    const baseChains = await ChainsAPI.updateBaseChains(mockBaseChainsData);

    expect(baseChains).toEqual(mockBaseChainsData);
    expect(fetch).toHaveBeenCalledTimes(2);
});

const alertsOverviewMockData = {
    result: { test_chain: { critical: 0, warning: 0, error: 0 } }
};

it('updateBaseChains() - same alerts', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
        json: () => Promise.resolve(monitorablesInfoMockData),
    })).mockImplementationOnce(() => Promise.resolve({
        json: () => Promise.resolve(alertsOverviewMockData),
    }));

    const baseChains = await ChainsAPI.updateBaseChains(mockBaseChainsData);

    expect(baseChains).toEqual(mockBaseChainsData);
    expect(fetch).toHaveBeenCalledTimes(2);
});


const alertsOverviewMockData2 = {
    result: { test_chain: { critical: 1, warning: 3, error: 2 } }
};

const mockBaseChainsData2 = [{
    name: 'cosmos', chains: [
        {
            name: 'test chain', id: 'test_chain', repos: ['test_repo'],
            systems: ['test_system'], criticalAlerts: 1, warningAlerts: 3,
            errorAlerts: 2, totalAlerts: 6, active: true
        }]
}];

it('updateBaseChains() - updated alerts', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
        json: () => Promise.resolve(monitorablesInfoMockData),
    })).mockImplementationOnce(() => Promise.resolve({
        json: () => Promise.resolve(alertsOverviewMockData2),
    }));

    const baseChains = await ChainsAPI.updateBaseChains(mockBaseChainsData);

    expect(baseChains).toEqual(mockBaseChainsData2);
    expect(fetch).toHaveBeenCalledTimes(2);
});
