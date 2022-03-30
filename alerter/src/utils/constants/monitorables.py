from enum import Enum


class MonitorableType(Enum):
    SYSTEMS = 'systems'
    NODES = 'nodes'
    GITHUB_REPOS = 'github_repos'
    DOCKERHUB_REPOS = 'dockerhub_repos'
    CHAINS = 'chains'


EMPTY_MONITORABLE_DATA = {
    'chain_name': '',
    MonitorableType.SYSTEMS.value: {},
    MonitorableType.NODES.value: {},
    MonitorableType.GITHUB_REPOS.value: {},
    MonitorableType.DOCKERHUB_REPOS.value: {},
    MonitorableType.CHAINS.value: {}
}

MONITORABLES_MONGO_COLLECTION = 'monitorables'
