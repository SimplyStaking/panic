import {BaseChain} from "../interfaces/chains";
import {FilterState} from "../interfaces/filterState";
import {FilterStateAPI} from "./filterState";
import {RepoType, Severity} from "./constants";

/**
 * Mocking {@link fetch} function.
 */
export const fetchMock: any = fetch as any;

/**
 * Mocking API response from `redis/monitorablesInfo` endpoint.
 */
export function mockMonitorablesInfoData(): any {
    return {
        result: {
            'cosmos': {},
            'general': {
                'test chain': {
                    parent_id: "test_chain",
                    monitored: {
                        systems: [{'test_system_id': 'test_system'}],
                        nodes: [
                          {'test_node_id': 'test_node'},
                          {'test_evm_node_id': 'test_evm_node'}
                        ],
                        github_repos: [{'test_repo_id': 'test_repo'}],
                        dockerhub_repos: [{'test_docker_id': 'test_repo2'}],
                        chains: [{'test_chain': 'general test chain'}]
                    }
                }
            },
            'chainlink': {},
            'substrate': {},
        }
    }
}

/**
 * Mocking API response from `mongo/alerts` endpoint.
 */
export function mockAlertsData(): any {
    return {
        result: {
            alerts: [
                {
                    severity: 'WARNING',
                    message: 'test alert 1',
                    timestamp: 1609459200,
                    origin: 'test_system_id'
                },
                {
                    severity: 'WARNING',
                    message: 'test alert 2',
                    timestamp: 1609459200,
                    origin: 'test_system_id'
                },
                {
                    severity: 'WARNING',
                    message: 'test alert 3',
                    timestamp: 1609459200,
                    origin: 'test_system_id'
                },
                {
                    severity: 'ERROR',
                    message: 'test alert 4',
                    timestamp: 1609459200,
                    origin: 'test_system_id'
                },
                {
                    severity: 'ERROR',
                    message: 'test alert 5',
                    timestamp: 1609459200,
                    origin: 'test_system_id'
                },
                {
                    severity: 'WARNING',
                    message: 'test alert 1',
                    timestamp: 1609459200,
                    origin: 'test_node_id'
                },
                {
                    severity: 'WARNING',
                    message: 'test alert 2',
                    timestamp: 1609459200,
                    origin: 'test_node_id'
                },
                {
                    severity: 'WARNING',
                    message: 'test alert 3',
                    timestamp: 1609459200,
                    origin: 'test_node_id'
                },
                {
                    severity: 'ERROR',
                    message: 'test alert 1',
                    timestamp: 1609459200,
                    origin: 'test_evm_node_id'
                },
                {
                    severity: 'ERROR',
                    message: 'test alert 2',
                    timestamp: 1609459200,
                    origin: 'test_evm_node_id'
                }
            ]
        }
    }
}

/**
 * Mocking API response from `redis/metrics` endpoint.
 */
export function mockMetricsData(): any {
    return {
        result: {
            test_chain: {
                system: {
                    test_system_id: {
                        s1: "20958.95",
                        s2: "0.50",
                        s3: "119562240.0",
                        s4: "0.78125",
                        s5: "3.08",
                        s6: "26.87",
                        s7: "19.31",
                        s8: "321182.1313708029",
                        s9: "336986.0599286745",
                        s10: "9072582636432.0",
                        s11: "9897442929052.0",
                        s12: "2046614.708",
                        s13: "1.4879999998956919",
                        s14: "1635838422.939961",
                        s15: "None"
                    }
                }
            }
        }
    }
}

/**
 * Mocking an array of base chains with a single repo, a single system, and no
 * alerts.
 */
export function mockBaseChainsData(): BaseChain[] {
    return [{
        name: 'general',
        subChains: [
            {
                name: 'test chain',
                id: 'test_chain',
                systems: [{id: 'test_system_id', name: "test_system"}],
                nodes: [{id: 'test_node_id', name: "test_node"},
                    {id: 'test_evm_node_id', name: "test_evm_node"}],
                repos: [{id: 'test_repo_id', name: "test_repo",
                    type: RepoType.GITHUB}],
                isSource: false,
                alerts: []
            }]
    }]
}

export function mockFilterStates(): FilterState[] {
    return FilterStateAPI.getFilterStates(mockBaseChainsData(), []);
}

/**
 * Mocking API response (no alerts) from `redis/alertsOverview` endpoint.
 */
export function mockAlertsOverviewNoAlerts(): any {
    return {
        result: {test_chain: {critical: 0, warning: 0, error: 0}}
    }
}

/**
 * Mocking API response from `redis/alertsOverview` endpoint.
 */
export function mockAlertsOverviewWithAlerts(): any {
    return {
        result: {
            test_chain: {
                critical: 1,
                warning: 3,
                error: 2,
                problems: {
                    test_chain: [
                        {
                            severity: 'WARNING',
                            message: 'test alert 1',
                            timestamp: 12345,
                            origin: 'test_system_id'
                        },
                        {
                            severity: 'WARNING',
                            message: 'test alert 2',
                            timestamp: 12345,
                            origin: 'test_system_id'
                        },
                        {
                            severity: 'WARNING',
                            message: 'test alert 3',
                            timestamp: 12345,
                            origin: 'test_system_id'
                        },
                        {
                            severity: 'ERROR',
                            message: 'test alert 4',
                            timestamp: 12345,
                            origin: 'test_system_id'
                        },
                        {
                            severity: 'ERROR',
                            message: 'test alert 5',
                            timestamp: 12345,
                            origin: 'test_system_id'
                        },
                        {
                            severity: 'WARNING',
                            message: 'test alert 1',
                            timestamp: 12345,
                            origin: 'test_node_id'
                        },
                        {
                            severity: 'WARNING',
                            message: 'test alert 2',
                            timestamp: 12345,
                            origin: 'test_node_id'
                        },
                        {
                            severity: 'WARNING',
                            message: 'test alert 3',
                            timestamp: 12345,
                            origin: 'test_node_id'
                        },
                        {
                            severity: 'WARNING',
                            message: 'test alert 1',
                            timestamp: 12345,
                            origin: 'test_evm_node_id'
                        },
                        {
                            severity: 'WARNING',
                            message: 'test alert 2',
                            timestamp: 12345,
                            origin: 'test_evm_node_id'
                        }
                    ]
                }
            }
        }
    }
}

/**
 * Mocking an array of base chains with populated alerts.
 */
export function mockBaseChainsDataWithAlerts(): BaseChain[] {
    const mockBaseChainsDataWithAlertsData: BaseChain[] = [...mockBaseChainsData()];
    mockBaseChainsDataWithAlertsData[0].subChains[0].alerts.push(
        {
            severity: 'WARNING' as Severity,
            message: 'test alert 1',
            timestamp: 12345,
            origin: null
        },
        {
            severity: 'WARNING' as Severity,
            message: 'test alert 2',
            timestamp: 12345,
            origin: null
        },
        {
            severity: 'WARNING' as Severity,
            message: 'test alert 3',
            timestamp: 12345,
            origin: null
        },
        {
            severity: 'ERROR' as Severity,
            message: 'test alert 4',
            timestamp: 12345,
            origin: null
        },
        {
            severity: 'ERROR' as Severity,
            message: 'test alert 5',
            timestamp: 12345,
            origin: null
        },
        {
          severity: 'WARNING' as Severity,
          message: 'test alert 1',
          timestamp: 12345,
          origin: null
        },
        {
          severity: 'WARNING' as Severity,
          message: 'test alert 2',
          timestamp: 12345,
          origin: null
        },
        {
          severity: 'WARNING' as Severity,
          message: 'test alert 3',
          timestamp: 12345,
          origin: null
        },
        {
          severity: 'WARNING' as Severity,
          message: 'test alert 1',
          timestamp: 12345,
          origin: null
        },
        {
          severity: 'WARNING' as Severity,
          message: 'test alert 2',
          timestamp: 12345,
          origin: null
        });

    return mockBaseChainsDataWithAlertsData;
}
