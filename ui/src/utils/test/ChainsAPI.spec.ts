import {ChainsAPI} from "../chains";
import {BASE_CHAINS, RepoType} from "../constants";
import {
    fetchMock,
    mockAlertsOverviewNoAlerts,
    mockAlertsOverviewWithAlerts,
    mockBaseChainsData,
    mockBaseChainsDataWithAlerts,
    mockFilterStates,
    mockMonitorablesInfoData
} from "../mock";

beforeEach(() => {
    fetchMock.resetMocks();
});

describe('getBaseChains() function', () => {
    it('should return an empty array when chain API is down', async () => {
        fetchMock.mockReject(() => Promise.reject("API is down"));
        const baseChains = await ChainsAPI.getAllBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should return an empty array when there are no base chains', async () => {
        const monitorablesInfoNoBaseChains: any = mockMonitorablesInfoData();
        monitorablesInfoNoBaseChains.result['general'] = null;

        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfoNoBaseChains));
        const baseChains = await ChainsAPI.getAllBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should not return a base chain if it does not contain any chains', async () => {
        const monitorablesInfo1BaseChain0Chains: any = mockMonitorablesInfoData();
        monitorablesInfo1BaseChain0Chains.result['general'] = {};

        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfo1BaseChain0Chains));
        const baseChains = await ChainsAPI.getAllBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should not return a base chain if none of its chains have the monitored field', async () => {
        const monitorablesInfoWithoutMonitored: any = mockMonitorablesInfoData();
        delete monitorablesInfoWithoutMonitored.result['general']['test chain'].monitored;

        monitorablesInfoWithoutMonitored.result[BASE_CHAINS[0]] = {'test chain': {parent_id: "test_chain"}};
        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfoWithoutMonitored));
        const baseChains = await ChainsAPI.getAllBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should not return a base chain if no sources are available within its chains', async () => {
        const monitorablesInfoEmptyMonitored: any = mockMonitorablesInfoData();
        monitorablesInfoEmptyMonitored.result['general']['test chain'].monitored = {};

        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfoEmptyMonitored));
        const baseChains = await ChainsAPI.getAllBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should not return a base chain if no systems, nodes, repos, or chains are available within its chains', async () => {
        const monitorablesInfoNoSources: any = mockMonitorablesInfoData();
        monitorablesInfoNoSources.result['general']['test chain'].monitored.systems = [];
        monitorablesInfoNoSources.result['general']['test chain'].monitored.nodes = [];
        monitorablesInfoNoSources.result['general']['test chain'].monitored.github_repos = [];
        monitorablesInfoNoSources.result['general']['test chain'].monitored.dockerhub_repos = [];
        monitorablesInfoNoSources.result['general']['test chain'].monitored.chains = [];

        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfoNoSources));
        const baseChains = await ChainsAPI.getAllBaseChains();

        expect(baseChains).toEqual([]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should return the base chain when its chains contain valid sources', async () => {
        fetchMock.mockResponseOnce(JSON.stringify(mockMonitorablesInfoData()));
        const baseChains = await ChainsAPI.getAllBaseChains();

        expect(baseChains).toEqual([{
            name: 'general',
            subChains: [{
                id: "test_chain", name: 'test chain',
                systems: [{id: 'test_system_id', name: 'test_system'}],
                nodes: [{id: 'test_node_id', name: 'test_node'},
                    {id: 'test_evm_node_id', name: 'test_evm_node'}],
                repos: [{id: 'test_repo_id', name: 'test_repo',
                    type: RepoType.GITHUB},
                    {id: 'test_docker_id', name: 'test_repo2',
                        type: RepoType.DOCKERHUB}],
                isSource: true,
                alerts: []
            }]
        }]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should return the base chain with false isSource when its chains do not contain chain sources', async () => {
        const monitorablesInfoEmptyChains: any = mockMonitorablesInfoData();
        monitorablesInfoEmptyChains.result['general']['test chain'].monitored.chains = [];
        fetchMock.mockResponseOnce(JSON.stringify(monitorablesInfoEmptyChains));
        const baseChains = await ChainsAPI.getAllBaseChains();

        expect(baseChains).toEqual([{
            name: 'general',
            subChains: [{
                id: "test_chain", name: 'test chain',
                systems: [{id: 'test_system_id', name: 'test_system'}],
                nodes: [{id: 'test_node_id', name: 'test_node'},
                    {id: 'test_evm_node_id', name: 'test_evm_node'}],
                repos: [{id: 'test_repo_id', name: 'test_repo',
                    type: RepoType.GITHUB},
                    {id: 'test_docker_id', name: 'test_repo2',
                        type: RepoType.DOCKERHUB}],
                isSource: false,
                alerts: []
            }]
        }]);
        expect(fetch).toHaveBeenCalledTimes(1);
    });
});

describe('updateBaseChainsWithAlerts() function', () => {
    it('should not add any alerts when API is down', async () => {
        fetchMock.mockReject(() => Promise.reject("API is down"));
        const baseChains = await ChainsAPI.updateBaseChainsWithAlerts(mockBaseChainsData(), mockFilterStates());

        expect(baseChains).toEqual(mockBaseChainsData());
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should not change base chains if alerts did not change', async () => {
        fetchMock.mockResponses([JSON.stringify(mockMonitorablesInfoData())],
            [JSON.stringify(mockAlertsOverviewNoAlerts())]);

        const baseChains = await ChainsAPI.updateBaseChainsWithAlerts(mockBaseChainsData(), mockFilterStates());

        expect(baseChains).toEqual(mockBaseChainsData());
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should update base chains if alerts changed', async () => {
        fetchMock.mockResponseOnce(JSON.stringify(mockAlertsOverviewWithAlerts()));

        const baseChains = await ChainsAPI.updateBaseChainsWithAlerts(mockBaseChainsData(), mockFilterStates());

        expect(baseChains).toEqual(mockBaseChainsDataWithAlerts());
        expect(fetch).toHaveBeenCalledTimes(1);
    });
});
