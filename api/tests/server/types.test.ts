import {
    isAlertsOverviewInputValid,
    isRedisMetricsInputValid
} from '../../src/server/types';

describe('isAlertsOverviewInputValid', () => {
    it.each([
        ['an empty body', {}],
        ['a single chain with no systems, nodes, or repos and chain sourced' +
        ' alerts true',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a single chain with no systems, nodes, or repos and chain sourced' +
        ' false',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': false,
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a single chain with a single system',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': ['test_system'],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a single chain with a single node',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': ['test_node'],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a single chain with a single github repo',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'github_repos': ['test_repo'],
                    'dockerhub_repos': []
                }
            }],
        ['a single chain with a single dockerhub repo',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': ['test_repo']
                }
            }],
        ['a single chain with a single system and a single node',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': ['test_system'],
                    'nodes': ['test_node'],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a single chain with a single system and a single repo',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': ['test_system'],
                    'nodes': [],
                    'github_repos': ['test_repo'],
                    'dockerhub_repos': []
                }
            }],
        ['a single chain with a single node and a single repo',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': ['test_node'],
                    'github_repos': ['test_repo'],
                    'dockerhub_repos': []
                }
            }],
        ['a single chain with a single system, a single node, and a single' +
        ' repo',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': ['test_system'],
                    'nodes': ['test_node'],
                    'github_repos': ['test_repo'],
                    'dockerhub_repos': []
                }
            }],
        ['a single chain with multiple systems, multiple nodes, and multiple' +
        ' repos',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': ['test_system', 'test_system2'],
                    'nodes': ['test_node', 'test_node2'],
                    'github_repos': ['test_repo', 'test_repo2'],
                    'dockerhub_repos': ['test_repo3', 'test_repo4']
                }
            }],
        ['multiple chains with no systems or repos',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                },
                'test_chain2': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['multiple chains with a single system',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': ['test_system'],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                },
                'test_chain2': {
                    'include_chain_sourced_alerts': true,
                    'systems': ['test_system2'],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['multiple chains with a single repo',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'github_repos': ['test_repo'],
                    'dockerhub_repos': []
                },
                'test_chain2': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': ['test_repo2']
                }
            }],
        ['multiple chains with a single system, a single node, and a single' +
        ' repo',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': ['test_system'],
                    'nodes': ['test_node'],
                    'github_repos': ['test_repo'],
                    'dockerhub_repos': []
                },
                'test_chain2': {
                    'include_chain_sourced_alerts': true,
                    'systems': ['test_system2'],
                    'nodes': ['test_node'],
                    'github_repos': [],
                    'dockerhub_repos': ['test_repo2']
                }
            }],
        ['multiple chains with multiple systems, multiple nodes, and multiple' +
        ' repos',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': ['test_system', 'test_system2'],
                    'nodes': ['test_node', 'test_node2'],
                    'github_repos': ['test_repo', 'test_repo2'],
                    'dockerhub_repos': ['test_repo3', 'test_repo4']
                },
                'test_chain2': {
                    'include_chain_sourced_alerts': true,
                    'systems': ['test_system3', 'test_system4'],
                    'nodes': ['test_node3', 'test_node4'],
                    'github_repos': ['test_repo5', 'test_repo6'],
                    'dockerhub_repos': ['test_repo7', 'test_repo8']
                }
            }]
    ])('Should return true if object consists of %s',
        async (_: string, object: any) => {
            const ret: boolean = isAlertsOverviewInputValid(object);
            expect(ret).toEqual(true);
        });

    it.each([
        ['a number', 123],
        ['a string', 'test'],
        ['null', null],
        ['an array', ['test', 123, null]],
        ['a chain without include_chain_sourced_alerts, systems, nodes, and' +
        ' repos fields',
            {
                'test_chain': {}
            }],
        ['a chain without include_chain_sourced_alerts field',
            {
                'test_chain': {
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain without systems field',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain without repos fields',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': []
                }
            }],
        ['a chain without github repos fields',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain without dockerhub repos fields',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'github_repos': []
                }
            }],
        ['a chain with invalid include_chain_sourced_alerts field (number)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': 123,
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid include_chain_sourced_alerts field (list)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': [],
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid include_chain_sourced_alerts field (object)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': {},
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid include_chain_sourced_alerts field (null)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': null,
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid include_chain_sourced_alerts field (string)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': 'test',
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid systems field (number)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': 123,
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid nodes field (number)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': 123,
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid github repos field (string)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'github_repos': 'test',
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid dockerhub repos field (string)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'github_repos': 'test',
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid types in systems field (number)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [123],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid types in nodes field (number)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [123],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid types in systems field (null)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [null],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid types in nodes field (null)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [null],
                    'github_repos': [],
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid types in github repos field (object)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'github_repos': [{}],
                    'dockerhub_repos': []
                }
            }],
        ['a chain with invalid types in dockerhub repos field (object)',
            {
                'test_chain': {
                    'include_chain_sourced_alerts': true,
                    'systems': [],
                    'nodes': [],
                    'github_repos': [],
                    'dockerhub_repos': [{}]
                }
            }],
    ])('Should return false if object consists of %s',
        async (_: string, object: any) => {
            const ret: boolean = isRedisMetricsInputValid(object);
            expect(ret).toEqual(false);
        });
});

describe('isRedisMetricsInputValid', () => {
    it.each([
        ['an empty body',
            {}],
        ['a single chain with no systems or repos',
            {
                'test_chain': {
                    'systems': [],
                    'repos': []
                }
            }],
        ['a single chain with a single system',
            {
                'test_chain': {
                    'systems': ['test_system'],
                    'repos': []
                }
            }],
        ['a single chain with a single repo',
            {
                'test_chain': {
                    'systems': [],
                    'repos': ['test_repo']
                }
            }],
        ['a single chain with a single system and a single repo',
            {
                'test_chain': {
                    'systems': ['test_system'],
                    'repos': ['test_repo']
                }
            }],
        ['a single chain with multiple systems and multiple repos',
            {
                'test_chain': {
                    'systems': ['test_system', 'test_system2'],
                    'repos': ['test_repo', 'test_repo2']
                }
            }],
        ['multiple chains with no systems or repos',
            {
                'test_chain': {
                    'systems': [],
                    'repos': []
                },
                'test_chain2': {
                    'systems': [],
                    'repos': []
                }
            }],
        ['multiple chains with a single system',
            {
                'test_chain': {
                    'systems': ['test_system'],
                    'repos': []
                },
                'test_chain2': {
                    'systems': ['test_system2'],
                    'repos': []
                }
            }],
        ['multiple chains with a single repo',
            {
                'test_chain': {
                    'systems': [],
                    'repos': ['test_repo']
                },
                'test_chain2': {
                    'systems': [],
                    'repos': ['test_repo2']
                }
            }],
        ['multiple chains with a single system and a single repo',
            {
                'test_chain': {
                    'systems': ['test_system'],
                    'repos': ['test_repo']
                },
                'test_chain2': {
                    'systems': ['test_system2'],
                    'repos': ['test_repo2']
                }
            }],
        ['multiple chains with multiple systems and multiple repos',
            {
                'test_chain': {
                    'systems': ['test_system', 'test_system2'],
                    'repos': ['test_repo', 'test_repo2']
                },
                'test_chain2': {
                    'systems': ['test_system3', 'test_system4'],
                    'repos': ['test_repo3', 'test_repo4']
                }
            }]
    ])('Should return true if object consists of %s',
        async (_: string, object: any) => {
            const ret: boolean = isRedisMetricsInputValid(object);
            expect(ret).toEqual(true);
        });

    it.each([
        ['a number', 123],
        ['a string', 'test'],
        ['null', null],
        ['an array', ['test', 123, null]],
        ['a chain without systems and repos fields',
            {
                'test_chain': {}
            }],
        ['a chain without systems field',
            {
                'test_chain': {
                    'repos': [],
                }
            }],
        ['a chain without repos field',
            {
                'test_chain': {
                    'systems': [],
                }
            }],
        ['a chain with invalid systems field (number)',
            {
                'test_chain': {
                    'systems': 123,
                    'repos': []
                }
            }],
        ['a chain with invalid repos field (string)',
            {
                'test_chain': {
                    'systems': [],
                    'repos': 'test'
                }
            }],
        ['a chain with invalid types in systems field (number)',
            {
                'test_chain': {
                    'systems': [123],
                    'repos': []
                }
            }],
        ['a chain with invalid types in systems field (null)',
            {
                'test_chain': {
                    'systems': [null],
                    'repos': []
                }
            }],
        ['a chain with invalid types in repos field (object)',
            {
                'test_chain': {
                    'systems': [],
                    'repos': [{}]
                }
            }],
    ])('Should return false if object consists of %s',
        async (_: string, object: any) => {
            const ret: boolean = isRedisMetricsInputValid(object);
            expect(ret).toEqual(false);
        });
});
