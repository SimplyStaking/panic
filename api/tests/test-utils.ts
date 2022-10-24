import axios, {AxiosResponse} from "axios";

export {
    // Common
    axiosMock,
    emptyAxiosResponse,
    parentIdsInvalidSchemaError,

    // Mongo - Monitorables Info
    monitorablesInfoSingleSourceMongoRet,
    monitorablesInfoSingleSourceEndpointRet,
    monitorablesInfoMultipleSourcesMongoRet,
    monitorablesInfoMultipleSourcesEndpointRet,
    monitorablesInfoMultipleSourcesAndBaseChainsMongoRet,
    monitorablesInfoMultipleSourcesAndBaseChainsEndpointRet,
    monitorablesInfoInvalidBaseChainsError,

    // Mongo - Alerts
    alertsSingleSourceMongoRet,
    alertsSingleSourceEndpointRet,
    alertsMultipleSourcesMongoRet,
    alertsMultipleSourcesEndpointRet,

    // Mongo - Metrics
    metricsSingleSystemMongoRet,
    metricsSingleSystemEndpointRet,
    metricsMultipleSystemsMongoRet,
    metricsMultipleSystemsEndpointRet,

    // Redis - Alerts Overview
    alertsOverviewSingleSystemRedisRet,
    alertsOverviewSingleSystemEndpointRet,
    alertsOverviewSingleNodeRedisRet,
    alertsOverviewSingleNodeEndpointRet,
    alertsOverviewSingleGitHubRepoRedisRet,
    alertsOverviewSingleGitHubRepoEndpointRet,
    alertsOverviewSingleDockerHubRepoRedisRet,
    alertsOverviewSingleDockerHubRepoEndpointRet,
    alertsOverviewChainSourceRedisRet,
    alertsOverviewChainSourceEndpointRet,
    alertsOverviewChainSourceWithUniqueIdentifierRedisRet,
    alertsOverviewChainSourceWithUniqueIdentifierEndpointRet,
    alertsOverviewMultipleSourcesRedisRet,
    alertsOverviewMultipleSourcesEndpointRet,

    // Redis - Metrics
    noMetricsSingleSystemRedisRet,
    noMetricsSingleSystemRedisEndpointRet,
    noMetricsSingleRepoRedisRet,
    noMetricsSingleRepoRedisEndpointRet,
    metricsSingleSystemRedisRet,
    metricsSingleSystemRedisEndpointRet,
    metricsSingleRepoRedisRet,
    metricsSingleRepoRedisEndpointRet,
}

// Common

/**
 * Mocking {@link axios} package.
 */
const axiosMock: any = axios as any;

const emptyAxiosResponse = (data: any = null): AxiosResponse => {
    return {
        config: null,
        headers: null,
        status: 200,
        statusText: 'OK',
        data
    }
};

const parentIdsInvalidSchemaError: string = 'Error: req.body.parentIds ' +
    'does not obey the required schema.';

// Mongo - Monitorables Info
const monitorablesInfoSingleSourceMongoRet: any[] = [
    {
        _id: "cosmos",
        'chain_name_611fc506-0339-4d63-ad67-851ca4be5fe1': {
            chain_name: 'cosmos',
            systems: {
                'system_f11cf285-d204-4ea6-9272-43c8b84fef07': {
                    name: 'cosmos_system_1',
                    manager_names: ['System Monitors Manager']
                }
            },
            nodes: {},
            github_repos: {},
            dockerhub_repos: {},
            chains: {}
        }
    }
];

const monitorablesInfoSingleSourceEndpointRet: any = {
    result: {
        cosmos: {
            cosmos: {
                parent_id: 'chain_name_611fc506-0339-4d63-ad67-851ca4be5fe1',
                monitored: {
                    systems: [
                        {
                            'system_f11cf285-d204-4ea6-9272-43c8b84fef07':
                                'cosmos_system_1'
                        }
                    ],
                    nodes: [],
                    github_repos: [],
                    dockerhub_repos: [],
                    chains: []
                }
            }
        },
        general: {},
        chainlink: {},
        substrate: {}
    }
};

const monitorablesInfoMultipleSourcesMongoRet: any[] = [
    {
        _id: "cosmos",
        'chain_name_611fc506-0339-4d63-ad67-851ca4be5fe1': {
            chain_name: 'cosmos',
            systems: {
                'system_f11cf285-d204-4ea6-9272-43c8b84fef07': {
                    name: 'cosmos_system_1',
                    manager_names: ['System Monitors Manager']
                },
                'system_f11cf285-d204-4ea6-9272-43c8b84fef42': {
                    name: 'cosmos_system_2',
                    manager_names: ['System Monitors Manager']
                }
            },
            nodes: {
                'node_f11cf285-d204-4ea6-9272-43c8b84fef07': {
                    name: 'cosmos_node_1',
                    manager_names: ['Node Monitors Manager']
                },
                'node_f11cf285-d204-4ea6-9272-43c8b84fef42': {
                    name: 'cosmos_node_2',
                    manager_names: ['Node Monitors Manager']
                }
            },
            github_repos: {
                'repo_f11cf285-d204-4ea6-9272-43c8b84fef07': {
                    name: 'test/repo',
                    manager_names: ['GitHub Monitors Manager']
                }
            },
            dockerhub_repos: {},
            chains: {}
        }
    }
];

const monitorablesInfoMultipleSourcesEndpointRet: any = {
    result: {
        cosmos: {
            cosmos: {
                parent_id: 'chain_name_611fc506-0339-4d63-ad67-851ca4be5fe1',
                monitored: {
                    systems: [
                        {
                            'system_f11cf285-d204-4ea6-9272-43c8b84fef07':
                                'cosmos_system_1'
                        },
                        {
                            'system_f11cf285-d204-4ea6-9272-43c8b84fef42':
                                'cosmos_system_2'
                        }
                    ],
                    nodes: [
                        {
                            'node_f11cf285-d204-4ea6-9272-43c8b84fef07':
                                'cosmos_node_1'
                        },
                        {
                            'node_f11cf285-d204-4ea6-9272-43c8b84fef42':
                                'cosmos_node_2'
                        }
                    ],
                    github_repos: [
                        {
                            'repo_f11cf285-d204-4ea6-9272-43c8b84fef07':
                                'test/repo'
                        }
                    ],
                    dockerhub_repos: [],
                    chains: []
                }
            }
        },
        general: {},
        chainlink: {},
        substrate: {}
    }
};

const monitorablesInfoMultipleSourcesAndBaseChainsMongoRet: any[] = [
    {
        _id: "cosmos",
        'chain_name_611fc506-0339-4d63-ad67-851ca4be5fe1': {
            chain_name: 'cosmos',
            systems: {
                'system_f11cf285-d204-4ea6-9272-43c8b84fef07': {
                    name: 'cosmos_system_1',
                    manager_names: ['System Monitors Manager']
                },
                'system_f11cf285-d204-4ea6-9272-43c8b84fef42': {
                    name: 'cosmos_system_2',
                    manager_names: ['System Monitors Manager']
                }
            },
            nodes: {},
            github_repos: {
                'repo_f11cf285-d204-4ea6-9272-43c8b84fef07': {
                    name: 'test/repo',
                    manager_names: ['GitHub Monitors Manager']
                }
            },
            dockerhub_repos: {},
            chains: {}
        }
    },
    {
        _id: 'chainlink',
        'chain_name_611fc506-0339-4d63-ad67-851ca4be5fe2': {
            chain_name: 'chainlink',
            systems: {},
            nodes: {
                'node_f11cf285-d204-4ea6-9272-43c8b84fef08': {
                    name: 'cl_node_1',
                    manager_names: ['Node Monitors Manager']
                },
                'node_f11cf285-d204-4ea6-9272-43c8b84fef43': {
                    name: 'cl_node_2',
                    manager_names: ['Node Monitors Manager']
                },
                'node_f11cf285-d204-4ea6-9272-43c8b84fef82': {
                    name: 'cl_evm_node_1',
                    manager_names: ['Node Monitors Manager']
                }
            },
            github_repos: {},
            dockerhub_repos: {
                'docker_f11cf285-d204-4ea6-9272-43c8b84fef07': {
                    name: 'test/repo2',
                    manager_names: ['DockerHub Monitors Manager']
                }
            },
            chains: {
                'chain_name_611fc506-0339-4d63-ad67-851ca4be5fe2': {
                    name: 'chainlink',
                    manager_names: ['Contract Monitors Manager']
                }
            }
        }
    }
];

const monitorablesInfoMultipleSourcesAndBaseChainsEndpointRet: any = {
    result: {
        cosmos: {
            cosmos: {
                parent_id: 'chain_name_611fc506-0339-4d63-ad67-851ca4be5fe1',
                monitored: {
                    systems: [
                        {
                            'system_f11cf285-d204-4ea6-9272-43c8b84fef07':
                                'cosmos_system_1'
                        },
                        {
                            'system_f11cf285-d204-4ea6-9272-43c8b84fef42':
                                'cosmos_system_2'
                        }
                    ],
                    nodes: [],
                    github_repos: [
                        {
                            'repo_f11cf285-d204-4ea6-9272-43c8b84fef07':
                                'test/repo'
                        }
                    ],
                    dockerhub_repos: [],
                    chains: []
                }
            }
        },
        general: {},
        chainlink: {
            chainlink: {
                parent_id: 'chain_name_611fc506-0339-4d63-ad67-851ca4be5fe2',
                monitored: {
                    systems: [],
                    nodes: [
                        {
                            'node_f11cf285-d204-4ea6-9272-43c8b84fef08':
                                'cl_node_1'
                        },
                        {
                            'node_f11cf285-d204-4ea6-9272-43c8b84fef43':
                                'cl_node_2'
                        },
                        {
                            'node_f11cf285-d204-4ea6-9272-43c8b84fef82':
                                'cl_evm_node_1'
                        }
                    ],
                    github_repos: [],
                    dockerhub_repos: [
                        {
                            'docker_f11cf285-d204-4ea6-9272-43c8b84fef07':
                                'test/repo2'
                        }
                    ],
                    chains: [
                        {
                            'chain_name_611fc506-0339-4d63-ad67-851ca4be5fe2':
                                'chainlink'
                        }
                    ]
                }
            }
        },
        substrate: {}
    }
};

const monitorablesInfoInvalidBaseChainsError: string = 'Error: Invalid base ' +
    'chain(s) test. Please enter a list containing some of these values: ' +
    'cosmos, substrate, chainlink, general.';

// Mongo - Alerts
const alertsSingleSourceMongoRet: any[] = [
    {
        alerts: [
            {
                'origin': 'test_source',
                'alert_name': 'SystemWentDownAtAlert',
                'severity': 'CRITICAL',
                'message': 'test_source System is down, last time checked: ' +
                    '2021-11-08 15:38:54.547124.',
                'metric': 'system_is_down',
                'timestamp': 1636385934.547124
            },
            {
                'origin': 'test_source',
                'alert_name': 'SystemStorageUsageIncreasedAboveThresholdAlert',
                'severity': 'WARNING',
                'message': 'test_source system storage usage INCREASED above ' +
                    'WARNING Threshold. Current value: 87.82%.',
                'metric': 'system_storage_usage',
                'timestamp': 1636380204.517611
            }
        ]
    }
];

const alertsSingleSourceEndpointRet: any = {
    result: {
        alerts: [
            {
                'origin': 'test_source',
                'alert_name': 'SystemWentDownAtAlert',
                'severity': 'CRITICAL',
                'message': 'test_source System is down, last time checked: ' +
                    '2021-11-08 15:38:54.547124.',
                'metric': 'system_is_down',
                'timestamp': 1636385934.547124
            },
            {
                'origin': 'test_source',
                'alert_name': 'SystemStorageUsageIncreasedAboveThresholdAlert',
                'severity': 'WARNING',
                'message': 'test_source system storage usage INCREASED above ' +
                    'WARNING Threshold. Current value: 87.82%.',
                'metric': 'system_storage_usage',
                'timestamp': 1636380204.517611
            }
        ]
    }
};

const alertsMultipleSourcesMongoRet: any[] = [
    {
        alerts: [
            {
                'origin': 'test_node',
                'alert_name': 'SystemWentDownAtAlert',
                'severity': 'CRITICAL',
                'message': 'test_source System is down, last time checked: ' +
                    '2021-11-08 15:38:54.547124.',
                'metric': 'system_is_down',
                'timestamp': 1636385934.547124
            },
            {
                'origin': 'test_node',
                'alert_name': 'SystemStorageUsageIncreasedAboveThresholdAlert',
                'severity': 'WARNING',
                'message': 'test_source system storage usage INCREASED above ' +
                    'WARNING Threshold. Current value: 87.82%.',
                'metric': 'system_storage_usage',
                'timestamp': 1636380204.517611
            },
            {
                'origin': 'test_repo',
                'alert_name': 'NewGitHubReleaseAlert',
                'severity': 'INFO',
                'message': 'Repo: test/testrepo/ has a new release V1.0.0 ' +
                    'tagged V1.0.0.',
                'metric': 'github_release',
                'timestamp': 1636380204.517611
            }
        ]
    }
];

const alertsMultipleSourcesEndpointRet: any = {
    result: {
        alerts: [
            {
                'origin': 'test_node',
                'alert_name': 'SystemWentDownAtAlert',
                'severity': 'CRITICAL',
                'message': 'test_source System is down, last time checked: ' +
                    '2021-11-08 15:38:54.547124.',
                'metric': 'system_is_down',
                'timestamp': 1636385934.547124
            },
            {
                'origin': 'test_node',
                'alert_name': 'SystemStorageUsageIncreasedAboveThresholdAlert',
                'severity': 'WARNING',
                'message': 'test_source system storage usage INCREASED above ' +
                    'WARNING Threshold. Current value: 87.82%.',
                'metric': 'system_storage_usage',
                'timestamp': 1636380204.517611
            },
            {
                'origin': 'test_repo',
                'alert_name': 'NewGitHubReleaseAlert',
                'severity': 'INFO',
                'message': 'Repo: test/testrepo/ has a new release V1.0.0 ' +
                    'tagged V1.0.0.',
                'metric': 'github_release',
                'timestamp': 1636380204.517611
            }
        ]
    }
};

// Mongo - Metrics
const metricsSingleSystemMongoRet: any[] = [
    {
        test_system: {
            'process_cpu_seconds_total': '1689.55',
            'process_memory_usage': '0.0',
            'virtual_memory_usage': '735047680.0',
            'open_file_descriptors': '0.9765625',
            'system_cpu_usage': '26.13',
            'system_ram_usage': '12.94',
            'system_storage_usage': '87.95',
            'network_transmit_bytes_per_second': '1105951.4084449804',
            'network_receive_bytes_per_second': '1062237.540997162',
            'network_receive_bytes_total': '1236598884501.0',
            'network_transmit_bytes_total': '1300016543569.0',
            'disk_io_time_seconds_total': '789248.356',
            'disk_io_time_seconds_in_interval': '57.67200000002049',
            'went_down_at': 'None',
            'timestamp': 1636464102.394867
        }
    },
    {
        test_system: {
            'process_cpu_seconds_total': '1690.42',
            'process_memory_usage': '0.0',
            'virtual_memory_usage': '735047680.0',
            'open_file_descriptors': '0.9765625',
            'system_cpu_usage': '26.13',
            'system_ram_usage': '12.96',
            'system_storage_usage': '87.96',
            'network_transmit_bytes_per_second': '1108042.1411528764',
            'network_receive_bytes_per_second': '1062515.7000199233',
            'network_receive_bytes_total': '1237113219261.0',
            'network_transmit_bytes_total': '1300558677778.0',
            'disk_io_time_seconds_total': '789705.94',
            'disk_io_time_seconds_in_interval': '74.09599999990314',
            'went_down_at': 'None',
            'timestamp': 1636464584.351935
        }
    }
];

const metricsSingleSystemEndpointRet: any = {
    result: {
        metrics: {
            test_system: [
                {
                    'process_cpu_seconds_total': '1689.55',
                    'process_memory_usage': '0.0',
                    'virtual_memory_usage': '735047680.0',
                    'open_file_descriptors': '0.9765625',
                    'system_cpu_usage': '26.13',
                    'system_ram_usage': '12.94',
                    'system_storage_usage': '87.95',
                    'network_transmit_bytes_per_second': '1105951.4084449804',
                    'network_receive_bytes_per_second': '1062237.540997162',
                    'network_receive_bytes_total': '1236598884501.0',
                    'network_transmit_bytes_total': '1300016543569.0',
                    'disk_io_time_seconds_total': '789248.356',
                    'disk_io_time_seconds_in_interval': '57.67200000002049',
                    'went_down_at': 'None',
                    'timestamp': 1636464102.394867
                },
                {
                    'process_cpu_seconds_total': '1690.42',
                    'process_memory_usage': '0.0',
                    'virtual_memory_usage': '735047680.0',
                    'open_file_descriptors': '0.9765625',
                    'system_cpu_usage': '26.13',
                    'system_ram_usage': '12.96',
                    'system_storage_usage': '87.96',
                    'network_transmit_bytes_per_second': '1108042.1411528764',
                    'network_receive_bytes_per_second': '1062515.7000199233',
                    'network_receive_bytes_total': '1237113219261.0',
                    'network_transmit_bytes_total': '1300558677778.0',
                    'disk_io_time_seconds_total': '789705.94',
                    'disk_io_time_seconds_in_interval': '74.09599999990314',
                    'went_down_at': 'None',
                    'timestamp': 1636464584.351935
                }
            ]
        }
    }
};

const metricsMultipleSystemsMongoRet: any[] = [
    {
        test_system: {
            'process_cpu_seconds_total': '1689.55',
            'process_memory_usage': '0.0',
            'virtual_memory_usage': '735047680.0',
            'open_file_descriptors': '0.9765625',
            'system_cpu_usage': '26.13',
            'system_ram_usage': '12.94',
            'system_storage_usage': '87.95',
            'network_transmit_bytes_per_second': '1105951.4084449804',
            'network_receive_bytes_per_second': '1062237.540997162',
            'network_receive_bytes_total': '1236598884501.0',
            'network_transmit_bytes_total': '1300016543569.0',
            'disk_io_time_seconds_total': '789248.356',
            'disk_io_time_seconds_in_interval': '57.67200000002049',
            'went_down_at': 'None',
            'timestamp': 1636464102.394867
        }
    },
    {
        test_system: {
            'process_cpu_seconds_total': '1690.42',
            'process_memory_usage': '0.0',
            'virtual_memory_usage': '735047680.0',
            'open_file_descriptors': '0.9765625',
            'system_cpu_usage': '26.13',
            'system_ram_usage': '12.96',
            'system_storage_usage': '87.96',
            'network_transmit_bytes_per_second': '1108042.1411528764',
            'network_receive_bytes_per_second': '1062515.7000199233',
            'network_receive_bytes_total': '1237113219261.0',
            'network_transmit_bytes_total': '1300558677778.0',
            'disk_io_time_seconds_total': '789705.94',
            'disk_io_time_seconds_in_interval': '74.09599999990314',
            'went_down_at': 'None',
            'timestamp': 1636464584.351935
        }
    },
    {
        test_system2: {
            'process_cpu_seconds_total': '1689.55',
            'process_memory_usage': '0.0',
            'virtual_memory_usage': '735047680.0',
            'open_file_descriptors': '0.9765625',
            'system_cpu_usage': '26.13',
            'system_ram_usage': '12.94',
            'system_storage_usage': '87.95',
            'network_transmit_bytes_per_second': '1105951.4084449804',
            'network_receive_bytes_per_second': '1062237.540997162',
            'network_receive_bytes_total': '1236598884501.0',
            'network_transmit_bytes_total': '1300016543569.0',
            'disk_io_time_seconds_total': '789248.356',
            'disk_io_time_seconds_in_interval': '57.67200000002049',
            'went_down_at': 'None',
            'timestamp': 1636464102.394867
        }
    },
    {
        test_system2: {
            'process_cpu_seconds_total': '1690.42',
            'process_memory_usage': '0.0',
            'virtual_memory_usage': '735047680.0',
            'open_file_descriptors': '0.9765625',
            'system_cpu_usage': '26.13',
            'system_ram_usage': '12.96',
            'system_storage_usage': '87.96',
            'network_transmit_bytes_per_second': '1108042.1411528764',
            'network_receive_bytes_per_second': '1062515.7000199233',
            'network_receive_bytes_total': '1237113219261.0',
            'network_transmit_bytes_total': '1300558677778.0',
            'disk_io_time_seconds_total': '789705.94',
            'disk_io_time_seconds_in_interval': '74.09599999990314',
            'went_down_at': 'None',
            'timestamp': 1636464584.351935
        }
    }
];

const metricsMultipleSystemsEndpointRet: any = {
    result: {
        metrics: {
            test_system: [
                {
                    'process_cpu_seconds_total': '1689.55',
                    'process_memory_usage': '0.0',
                    'virtual_memory_usage': '735047680.0',
                    'open_file_descriptors': '0.9765625',
                    'system_cpu_usage': '26.13',
                    'system_ram_usage': '12.94',
                    'system_storage_usage': '87.95',
                    'network_transmit_bytes_per_second': '1105951.4084449804',
                    'network_receive_bytes_per_second': '1062237.540997162',
                    'network_receive_bytes_total': '1236598884501.0',
                    'network_transmit_bytes_total': '1300016543569.0',
                    'disk_io_time_seconds_total': '789248.356',
                    'disk_io_time_seconds_in_interval': '57.67200000002049',
                    'went_down_at': 'None',
                    'timestamp': 1636464102.394867
                },
                {
                    'process_cpu_seconds_total': '1690.42',
                    'process_memory_usage': '0.0',
                    'virtual_memory_usage': '735047680.0',
                    'open_file_descriptors': '0.9765625',
                    'system_cpu_usage': '26.13',
                    'system_ram_usage': '12.96',
                    'system_storage_usage': '87.96',
                    'network_transmit_bytes_per_second': '1108042.1411528764',
                    'network_receive_bytes_per_second': '1062515.7000199233',
                    'network_receive_bytes_total': '1237113219261.0',
                    'network_transmit_bytes_total': '1300558677778.0',
                    'disk_io_time_seconds_total': '789705.94',
                    'disk_io_time_seconds_in_interval': '74.09599999990314',
                    'went_down_at': 'None',
                    'timestamp': 1636464584.351935
                },
                null,
                null,
            ],
            test_system2: [
                null,
                null,
                {
                    'process_cpu_seconds_total': '1689.55',
                    'process_memory_usage': '0.0',
                    'virtual_memory_usage': '735047680.0',
                    'open_file_descriptors': '0.9765625',
                    'system_cpu_usage': '26.13',
                    'system_ram_usage': '12.94',
                    'system_storage_usage': '87.95',
                    'network_transmit_bytes_per_second': '1105951.4084449804',
                    'network_receive_bytes_per_second': '1062237.540997162',
                    'network_receive_bytes_total': '1236598884501.0',
                    'network_transmit_bytes_total': '1300016543569.0',
                    'disk_io_time_seconds_total': '789248.356',
                    'disk_io_time_seconds_in_interval': '57.67200000002049',
                    'went_down_at': 'None',
                    'timestamp': 1636464102.394867
                },
                {
                    'process_cpu_seconds_total': '1690.42',
                    'process_memory_usage': '0.0',
                    'virtual_memory_usage': '735047680.0',
                    'open_file_descriptors': '0.9765625',
                    'system_cpu_usage': '26.13',
                    'system_ram_usage': '12.96',
                    'system_storage_usage': '87.96',
                    'network_transmit_bytes_per_second': '1108042.1411528764',
                    'network_receive_bytes_per_second': '1062515.7000199233',
                    'network_receive_bytes_total': '1237113219261.0',
                    'network_transmit_bytes_total': '1300558677778.0',
                    'disk_io_time_seconds_total': '789705.94',
                    'disk_io_time_seconds_in_interval': '74.09599999990314',
                    'went_down_at': 'None',
                    'timestamp': 1636464584.351935
                }
            ]
        }
    }
};

// Redis - Alerts Overview
const alertsOverviewSingleSystemRedisRet: { [p: string]: string } = {
    'alert_system3_test_system': '{"severity": "WARNING", "message": ' +
        '"test_system system storage usage INCREASED above WARNING ' +
        'Threshold. Current value: 88.53%.", "metric": ' +
        '"system_storage_usage", "timestamp": 1636446847.232556, ' +
        '"expiry": null}',
    'alert_system5_test_system': '{"severity": "INFO", "message":' +
        ' "cosmos_node_1 System is back up, last successful monitor at:' +
        ' 2021-11-09 15:08:58.998260.", "metric": "system_is_down",' +
        ' "timestamp": 1636470538.99826, "expiry": null}'
}

const alertsOverviewSingleSystemEndpointRet: any = {
    result: {
        unique_chain_id: {
            info: 6, critical: 0, warning: 1, error: 0,
            problems: {
                test_system: [{
                    severity: 'WARNING',
                    message: 'test_system system storage usage INCREASED ' +
                        'above WARNING Threshold. Current value: 88.53%.',
                    metric: 'system_storage_usage',
                    timestamp: 1636446847.232556,
                    expiry: null
                }]
            },
            releases: {},
            tags: {}
        }
    }
};

const alertsOverviewSingleNodeRedisRet: { [p: string]: string } = {
    'alert_cl_node8_test_node': '{"severity": ' +
        '"WARNING", "message": "chainlink node Ethereum balance has DECREASED' +
        ' below WARNING threshold. Current value: 123.245.", "metric":' +
        ' "cl_eth_balance_amount", "timestamp": ' +
        '1636446847.232556, "expiry": null}',
    'alert_cl_node12_test_node': '{"severity": "INFO", "message": "chainlink' +
        ' node is back up, last successful monitor at: 2021-11-09' +
        ' 15:08:58.998260.", "metric" : "cl_node_is_down", "timestamp":' +
        ' 1636470538.99826, "expiry": null}',
    'alert_cl_contract1_test_node_0x12345': '{"severity": ' +
        '"CRITICAL", "message": "The Chainlink test_node node\'s' +
        ' submission has increased above CRITICAL threshold to 10% deviation' +
        ' for the price feed 0x12345. Current value: 123.456.", "metric":' +
        ' "cl_contract_price_feed_deviation", "timestamp": ' +
        '1636446847.232556, "expiry": null}',
}

const alertsOverviewSingleNodeEndpointRet: any = {
    result: {
        unique_chain_id: {
            info: 51, critical: 1, warning: 1, error: 0,
            problems: {
                test_node: [
                    {
                        severity: 'WARNING',
                        message: 'chainlink node Ethereum balance has DECREASED' +
                            ' below WARNING threshold. Current value: 123.245.',
                        metric: 'cl_eth_balance_amount',
                        timestamp: 1636446847.232556,
                        expiry: null
                    },
                    {
                        severity: 'CRITICAL',
                        message: 'The Chainlink test_node node\'s submission' +
                            ' has increased above CRITICAL threshold to 10%' +
                            ' deviation for the price feed 0x12345. Current' +
                            ' value: 123.456.',
                        metric: 'cl_contract_price_feed_deviation',
                        timestamp: 1636446847.232556,
                        expiry: null
                    }]
            },
            releases: {},
            tags: {}
        }
    }
};

const alertsOverviewSingleGitHubRepoRedisRet: { [p: string]: string } = {
    'alert_github1_test_repo': '{"severity": "INFO", "message": "Repo: ' +
        'test/testrepo/ has a new release V1.0.0 tagged V1.0.0.", "metric": ' +
        '"github_release", "timestamp": 1636446847.232556, "expiry": null}'
}

const alertsOverviewSingleGitHubRepoEndpointRet: any = {
    result: {
        unique_chain_id: {
            info: 3, critical: 0, warning: 0, error: 0,
            problems: {},
            releases: {
                test_repo: {
                    severity: 'INFO',
                    message: 'Repo: test/testrepo/ has a new release ' +
                        'V1.0.0 tagged V1.0.0.',
                    metric: 'github_release',
                    timestamp: 1636446847.232556,
                    expiry: null
                }
            },
            tags: {}
        }
    }
};

const alertsOverviewSingleDockerHubRepoRedisRet: { [p: string]: string } = {
    'alert_dockerhub1_test_repo': '{"severity": "INFO", "message": ' +
        '"Repo: test/testrepo/ has a new tag V1.0.0.", "metric": ' +
        '"dockerhub_new_tag", "timestamp": 1636446847.232556, "expiry": null}'
}

const alertsOverviewSingleDockerHubRepoEndpointRet: any = {
    result: {
        unique_chain_id: {
            info: 5, critical: 0, warning: 0, error: 0,
            problems: {},
            releases: {},
            tags: {
                test_repo: {
                    new: {
                        severity: 'INFO',
                        message: 'Repo: test/testrepo/ has a new tag V1.0.0.',
                        metric: 'dockerhub_new_tag',
                        timestamp: 1636446847.232556,
                        expiry: null
                    },
                    updated: {},
                    deleted: {}
                }
            }
        }
    }
};

const alertsOverviewChainSourceRedisRet: { [p: string]: string } = {
    'alert_cl_contract4': '{"severity": "ERROR", "message": ' +
        '"No synced data sources found.", "metric": ' +
        '"cl_contract_no_synced_data_sources", "timestamp": ' +
        '1636446847.232556, "expiry": null}'
}

const alertsOverviewChainSourceEndpointRet: any = {
    result: {
        unique_chain_id: {
            info: 0, critical: 0, warning: 0, error: 1,
            problems: {
                unique_chain_id: [{
                    severity: 'ERROR',
                    message: 'No synced data sources found.',
                    metric: 'cl_contract_no_synced_data_sources',
                    timestamp: 1636446847.232556,
                    expiry: null
                }]
            },
            releases: {},
            tags: {}
        }
    }
};

const alertsOverviewChainSourceWithUniqueIdentifierRedisRet: { [p: string]: string } = {
    'alert_cl_contract4': '{"severity": "WARNING", "message": ' +
        '"New proposal, ID: 123.", "metric": ' +
        '"substrate_network_proposal_submitted", "timestamp": ' +
        '1636446847.232556, "expiry": null}'
}

const alertsOverviewChainSourceWithUniqueIdentifierEndpointRet: any = {
    result: {
        unique_chain_id: {
            info: 0, critical: 0, warning: 1, error: 0,
            problems: {
                unique_chain_id: [{
                    severity: 'WARNING',
                    message: 'New proposal, ID: 123.',
                    metric: 'substrate_network_proposal_submitted',
                    timestamp: 1636446847.232556,
                    expiry: null
                }]
            },
            releases: {},
            tags: {}
        }
    }
};

const alertsOverviewMultipleSourcesRedisRet: { [p: string]: string } = {
    'alert_system3_test_system': '{"severity": "WARNING", "message": ' +
        '"test_system system storage usage INCREASED above WARNING ' +
        'Threshold. Current value: 88.53%.", "metric": ' +
        '"system_storage_usage", "timestamp": 1636446847.232556, ' +
        '"expiry": null}',
    'alert_system5_test_system': '{"severity": "INFO", "message":' +
        ' "System is back up, last successful monitor at:' +
        ' 2021-11-09 15:08:58.998260.", "metric": "system_is_down",' +
        ' "timestamp": 1636470538.99826, "expiry": null}',
    'alert_cl_node8_test_node': '{"severity": ' +
        '"WARNING", "message": "chainlink node Ethereum balance has DECREASED' +
        ' below WARNING threshold. Current value: 123.245.", "metric":' +
        ' "cl_eth_balance_amount", "timestamp": ' +
        '1636446847.232556, "expiry": null}',
    'alert_cl_node12_test_node': '{"severity": "INFO", "message": "chainlink' +
        ' node is back up, last successful monitor at: 2021-11-09' +
        ' 15:08:58.998260.", "metric" : "cl_node_is_down", "timestamp":' +
        ' 1636470538.99826, "expiry": null}',
    'alert_evm_node2_test_evm_node': '{"severity": ' +
        '"WARNING", "message": "evm node alert test message.", "metric":' +
        ' "evm_block_syncing_block_height_difference", "timestamp":' +
        ' 1636446847.232556, "expiry": null}',
    'alert_evm_node1_test_evm_node': '{"severity": "INFO", "message":' +
        ' "evm node is back up, last successful monitor at: 2021-11-09' +
        ' 15:08:58.998260.", "metric" : "evm_node_is_down", "timestamp":' +
        ' 1636470538.99826, "expiry": null}',
    'alert_github1_test_github_repo': '{"severity": "INFO", "message":' +
        ' "Repo: test/testrepo/ has a new release V1.0.0 tagged V1.0.0.", ' +
        '"metric": "github_release", "timestamp": 1636446847.232556, ' +
        '"expiry": null}',
    'alert_dockerhub1_test_dockerhub_repo': '{"severity": "INFO", "message": ' +
        '"Repo: test/testrepo/ has a new tag V1.0.0.", "metric": ' +
        '"dockerhub_new_tag", "timestamp": 1636446847.232556, "expiry": null}',
    'alert_cl_contract4': '{"severity": "ERROR", "message": ' +
        '"No synced data sources found.", "metric": ' +
        '"cl_contract_no_synced_data_sources", "timestamp": ' +
        '1636446847.232556, "expiry": null}',
    'alert_cosmos_network1': '{"severity": "CRITICAL", "message": ' +
        '"New proposal submitted: example proposal.", "metric": ' +
        '"cosmos_network_proposals_submitted", "timestamp": ' +
        '1636446847.232556, "expiry": null}',
    'alert_substrate_node1_test_node': '{"severity": "CRITICAL", "message": ' +
        '"Node is down.", "metric": ' +
        '"substrate_node_is_down", "timestamp": ' +
        '1636446847.232556, "expiry": null}',
    'alert_substrate_network1': '{"severity": "WARNING", "message": ' +
        '"Grandpa is stalled.", "metric": ' +
        '"substrate_network_grandpa_stalled", "timestamp": ' +
        '1636446847.232556, "expiry": null}'
}

const alertsOverviewMultipleSourcesEndpointRet: any = {
    result: {
        unique_chain_id: {
            info: 115, critical: 2, warning: 4, error: 1,
            problems: {
                test_system: [{
                    severity: 'WARNING',
                    message: 'test_system system storage usage INCREASED ' +
                        'above WARNING Threshold. Current value: 88.53%.',
                    metric: 'system_storage_usage',
                    timestamp: 1636446847.232556,
                    expiry: null
                }],
                test_evm_node: [{
                    severity: 'WARNING',
                    message: 'evm node alert test message.',
                    metric: 'evm_block_syncing_block_height_difference',
                    timestamp: 1636446847.232556,
                    expiry: null,
                }],
                test_node: [{
                    severity: 'WARNING',
                    message: 'chainlink node Ethereum balance has DECREASED' +
                        ' below WARNING threshold. Current value: 123.245.',
                    metric: 'cl_eth_balance_amount',
                    timestamp: 1636446847.232556,
                    expiry: null
                }, {
                    severity: 'CRITICAL',
                    message: 'Node is down.',
                    metric: 'substrate_node_is_down',
                    timestamp: 1636446847.232556,
                    expiry: null
                }],
                unique_chain_id: [{
                    severity: 'ERROR',
                    message: 'No synced data sources found.',
                    metric: 'cl_contract_no_synced_data_sources',
                    timestamp: 1636446847.232556,
                    expiry: null
                }, {
                    severity: 'CRITICAL',
                    message: 'New proposal submitted: example proposal.',
                    metric: 'cosmos_network_proposals_submitted',
                    timestamp: 1636446847.232556,
                    expiry: null
                }, {
                    severity: 'WARNING',
                    message: 'Grandpa is stalled.',
                    metric: 'substrate_network_grandpa_stalled',
                    timestamp: 1636446847.232556,
                    expiry: null
                }
                ],
            },
            releases: {
                test_github_repo: {
                    severity: 'INFO',
                    message: 'Repo: test/testrepo/ has a new release ' +
                        'V1.0.0 tagged V1.0.0.',
                    metric: 'github_release',
                    timestamp: 1636446847.232556,
                    expiry: null
                }
            },
            tags: {
                test_dockerhub_repo: {
                    new: {
                        severity: 'INFO',
                        message: 'Repo: test/testrepo/ has a new tag V1.0.0.',
                        metric: 'dockerhub_new_tag',
                        timestamp: 1636446847.232556,
                        expiry: null
                    },
                    updated: {},
                    deleted: {}
                }
            }
        }
    }
};

// Redis - Metrics
const noMetricsSingleSystemRedisRet: string[] = [
    'null', 'null', 'null', 'null',
    'null', 'null', 'null', 'null',
    'null', 'null', 'null', 'null',
    'null', 'null', 'null'
];

const noMetricsSingleSystemRedisEndpointRet: any = {
    result: {
        unique_chain_id: {
            system: {
                test_system: {
                    's1': 'null',
                    's2': 'null',
                    's3': 'null',
                    's4': 'null',
                    's5': 'null',
                    's6': 'null',
                    's7': 'null',
                    's8': 'null',
                    's9': 'null',
                    's10': 'null',
                    's11': 'null',
                    's12': 'null',
                    's13': 'null',
                    's14': 'null',
                    's15': 'null'
                }
            },
            github: {}
        }
    }
};

const noMetricsSingleRepoRedisRet: string[] = [
    'null', 'null'
];

const noMetricsSingleRepoRedisEndpointRet: any = {
    result: {
        unique_chain_id: {
            system: {},
            github: {
                test_repo: {
                    'gh1': 'null',
                    'gh2': 'null'
                }
            }
        }
    }
};

const metricsSingleSystemRedisRet: string[] = [
    '1709.16', '0.0',
    '735047680.0', '0.9765625',
    '26.22', '12.85',
    '88.05', '1252462.990811593',
    '1237515.5800031498', '1248558069305.0',
    '1312436132517.0', '801464.704',
    '69.6239999999525', '1636474994.58974',
    'None'
];

const metricsSingleSystemRedisEndpointRet: any = {
    result: {
        unique_chain_id: {
            system: {
                test_system: {
                    's1': '1709.16',
                    's2': '0.0',
                    's3': '735047680.0',
                    's4': '0.9765625',
                    's5': '26.22',
                    's6': '12.85',
                    's7': '88.05',
                    's8': '1252462.990811593',
                    's9': '1237515.5800031498',
                    's10': '1248558069305.0',
                    's11': '1312436132517.0',
                    's12': '801464.704',
                    's13': '69.6239999999525',
                    's14': '1636474994.58974',
                    's15': 'None'
                }
            },
            github: {}
        }
    }
};

const metricsSingleRepoRedisRet: string[] = [
    '7', '1635868064.122318'
];

const metricsSingleRepoRedisEndpointRet: any = {
    result: {
        unique_chain_id: {
            system: {},
            github: {
                test_repo: {
                    'gh1': '7',
                    'gh2': '1635868064.122318'
                }
            }
        }
    }
};
