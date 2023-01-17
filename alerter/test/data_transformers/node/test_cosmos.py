import copy
import json
import logging
import unittest
from datetime import datetime, timedelta
from queue import Queue
from unittest import mock

import pika
from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.data_store.redis import RedisApi
from src.data_transformers.node.cosmos import CosmosNodeDataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitorables.nodes.cosmos_node import CosmosNode
from src.utils import env
from src.utils.constants.cosmos import BOND_STATUS_BONDED
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, RAW_DATA_EXCHANGE, STORE_EXCHANGE, ALERT_EXCHANGE,
    COSMOS_NODE_DT_INPUT_QUEUE_NAME, COSMOS_NODE_RAW_DATA_ROUTING_KEY,
    HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
    COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
from src.utils.exceptions import (
    PANICException, NodeIsDownException, ReceivedUnexpectedDataException,
    MessageWasNotDeliveredException)
from test.test_utils.utils import (
    connect_to_rabbit, disconnect_from_rabbit, delete_exchange_if_exists,
    delete_queue_if_exists, save_cosmos_node_to_redis)


class TestCosmosNodeDataTransformer(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.test_data_str = 'test_data'
        self.transformer_name = 'test_cosmos_node_data_transformer'
        self.max_queue_size = 1000
        self.test_publishing_queue = Queue(self.max_queue_size)
        self.test_queue_name = 'Test Queue'
        self.test_last_monitored = datetime(2012, 1, 1).timestamp()
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'is_alive': True,
            'timestamp': self.test_last_monitored,
        }
        self.test_exception = PANICException('test_exception', 1)
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.invalid_transformed_data = {'bad_key': 'bad_value'}
        self.test_monitor_name = 'test_monitor_name'

        # Rabbit instance
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        # Redis Instance
        self.redis_db = env.REDIS_DB
        self.redis_host = env.REDIS_IP
        self.redis_port = env.REDIS_PORT
        self.redis_namespace = env.UNIQUE_ALERTER_IDENTIFIER
        self.redis = RedisApi(self.dummy_logger, self.redis_db,
                              self.redis_host, self.redis_port, '',
                              self.redis_namespace,
                              self.connection_check_time_interval)

        # Test node
        self.node_1 = CosmosNode('node_name_1', 'node_id_1', 'parent_id_1')
        self.test_is_validator = True
        self.test_operator_address = 'operator_address_1'
        self.test_node_is_down_exception = NodeIsDownException(
            self.node_1.node_name)
        self.test_state = {self.node_1.node_id: self.node_1}
        self.node_1.set_current_height(10000)
        self.node_1.set_voting_power(345456)
        self.node_1.set_is_syncing(False)
        self.node_1.set_bond_status(BOND_STATUS_BONDED)
        self.node_1.set_jailed(False)
        self.node_1.set_slashed(
            {
                'slashed': True,
                'amount_map': {
                    '4500': 50.4,
                    '4499': 23.4,
                    '4498': None,
                }
            }
        )
        self.node_1.set_missed_blocks(
            {
                'total_count': 2,
                'missed_heights': [4498, 4497]
            }
        )
        self.node_1.set_last_monitored_tendermint_rpc(self.test_last_monitored)
        self.node_1.set_last_monitored_cosmos_rest(self.test_last_monitored)
        self.node_1.set_last_monitored_prometheus(self.test_last_monitored)

        # Raw data examples
        self.raw_data_example_result_all = {
            'prometheus': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor_name,
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'data': {
                        'tendermint_consensus_latest_block_height': 10000.0,
                        'tendermint_consensus_validator_power': 345456.0,
                    },
                }
            },
            'cosmos_rest': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor_name,
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'data': {
                        'bond_status': BOND_STATUS_BONDED,
                        'jailed': False,
                    },
                }
            },
            'tendermint_rpc': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor_name,
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_mev_tendermint_node': False,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'data': {
                        'historical': [
                            {
                                'height': 4500,
                                'active_in_prev_block': False,
                                'signed_prev_block': False,
                                'slashed': True,
                                'slashed_amount': 50.4
                            },
                            {
                                'height': 4499,
                                'active_in_prev_block': True,
                                'signed_prev_block': False,
                                'slashed': True,
                                'slashed_amount': 23.4
                            },
                            {
                                'height': 4498,
                                'active_in_prev_block': True,
                                'signed_prev_block': False,
                                'slashed': True,
                                'slashed_amount': None
                            },
                        ],
                        'is_syncing': False,
                    },
                }
            }
        }

        self.raw_data_example_result_mev = copy.deepcopy(
            self.raw_data_example_result_all)
        self.raw_data_example_result_mev['tendermint_rpc']['result']['data']['is_peered_with_sentinel'] = True
        self.raw_data_example_result_mev['tendermint_rpc']['result']['meta_data']['is_mev_tendermint_node'] = True

        self.raw_data_example_result_options_None = copy.deepcopy(
            self.raw_data_example_result_all)
        self.raw_data_example_result_options_None['prometheus'][
            'result']['data']['tendermint_consensus_validator_power'] = None
        self.raw_data_example_result_options_None['tendermint_rpc']['result'][
            'data']['historical'] = None
        self.raw_data_example_result_options_None['tendermint_rpc']['result'][
            'data']['is_syncing'] = None
        self.raw_data_example_result_options_None['cosmos_rest']['result'][
            'data']['bond_status'] = None
        self.raw_data_example_result_options_None['cosmos_rest']['result'][
            'data']['jailed'] = None
        self.raw_data_example_general_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'monitor_name': self.test_monitor_name,
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            },
            'cosmos_rest': {
                'error': {
                    'meta_data': {
                        'monitor_name': self.test_monitor_name,
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            },
            'tendermint_rpc': {
                'error': {
                    'meta_data': {
                        'monitor_name': self.test_monitor_name,
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_mev_tendermint_node': False,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            }
        }
        self.raw_data_example_downtime_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'monitor_name': self.test_monitor_name,
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                }
            },
            'cosmos_rest': {
                'error': {
                    'meta_data': {
                        'monitor_name': self.test_monitor_name,
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                }
            },
            'tendermint_rpc': {
                'error': {
                    'meta_data': {
                        'monitor_name': self.test_monitor_name,
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_mev_tendermint_node': False,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                }
            }
        }

        # Transformed data examples
        self.transformed_data_example_result_all = {
            'prometheus': {
                'result': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'last_monitored': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'data': {
                        'current_height': 10000,
                        'voting_power': 345456,
                        'went_down_at': None,
                    },
                }
            },
            'cosmos_rest': {
                'result': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'last_monitored': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'data': {
                        'bond_status': BOND_STATUS_BONDED,
                        'jailed': False,
                        'went_down_at': None,
                    },
                }
            },
            'tendermint_rpc': {
                'result': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'last_monitored': self.test_last_monitored,
                        'is_mev_tendermint_node': False,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'data': {
                        'slashed': {
                            'slashed': True,
                            'amount_map': {
                                '4500': 50.4,
                                '4499': 23.4,
                                '4498': None,
                            }
                        },
                        'missed_blocks': {
                            'total_count': 2,
                            'missed_heights': [4498, 4497]
                        },
                        'is_syncing': False,
                        'went_down_at': None,
                    },
                }
            }
        }
        self.transformed_data_example_result_mev = copy.deepcopy(
            self.transformed_data_example_result_all)
        self.transformed_data_example_result_mev['tendermint_rpc']['result']['data']['is_peered_with_sentinel'] = True
        self.transformed_data_example_result_mev['tendermint_rpc']['result']['meta_data']['is_mev_tendermint_node'] = True


        self.transformed_data_example_result_options_None = copy.deepcopy(
            self.transformed_data_example_result_all)
        self.transformed_data_example_result_options_None['prometheus'][
            'result']['data']['voting_power'] = None
        self.transformed_data_example_result_options_None['tendermint_rpc'][
            'result']['data']['slashed'] = {
            'slashed': False,
            'amount_map': {}
        }
        self.transformed_data_example_result_options_None['tendermint_rpc'][
            'result']['data']['missed_blocks'] = {
            'total_count': 0,
            'missed_heights': []
        }
        self.transformed_data_example_result_options_None['tendermint_rpc'][
            'result']['data']['is_syncing'] = None
        self.transformed_data_example_result_options_None['cosmos_rest'][
            'result']['data']['bond_status'] = None
        self.transformed_data_example_result_options_None['cosmos_rest'][
            'result']['data']['jailed'] = None
        self.transformed_data_example_general_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            },
            'cosmos_rest': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            },
            'tendermint_rpc': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_mev_tendermint_node': False,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            }
        }
        self.transformed_data_example_downtime_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                    'data': {
                        'went_down_at': self.test_last_monitored
                    }
                }
            },
            'cosmos_rest': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                    'data': {
                        'went_down_at': self.test_last_monitored
                    }
                }
            },
            'tendermint_rpc': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_mev_tendermint_node': False,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                    'data': {
                        'went_down_at': self.test_last_monitored
                    }
                }
            }
        }

        # Processed data examples
        self.processed_data_example_result_all = {
            'prometheus': {
                'result': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'last_monitored': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'data': {
                        'current_height': {'current': 10000, 'previous': None},
                        'voting_power': {'current': 345456, 'previous': None},
                        'went_down_at': {'current': None, 'previous': None},
                    },
                }
            },
            'cosmos_rest': {
                'result': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'last_monitored': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'data': {
                        'bond_status': {
                            'current': BOND_STATUS_BONDED,
                            'previous': None
                        },
                        'jailed': {
                            'current': False,
                            'previous': None
                        },
                        'went_down_at': {'current': None, 'previous': None},
                    },
                }
            },
            'tendermint_rpc': {
                'result': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'last_monitored': self.test_last_monitored,
                        'is_mev_tendermint_node': False,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'data': {
                        'slashed': {
                            'current': {
                                'slashed': True,
                                'amount_map': {
                                    '4500': 50.4,
                                    '4499': 23.4,
                                    '4498': None,
                                }
                            },
                            'previous': {
                                'slashed': False,
                                'amount_map': {}
                            }
                        },
                        'missed_blocks': {
                            'current': {
                                'total_count': 2,
                                'missed_heights': [4498, 4497]
                            },
                            'previous': {
                                'total_count': 0,
                                'missed_heights': []
                            },
                        },
                        'is_syncing': {'current': False, 'previous': None},
                        'went_down_at': {'current': None, 'previous': None},
                    },
                }
            }
        }

        self.processed_data_example_result_all_mev = copy.deepcopy(
            self.processed_data_example_result_all)
        self.processed_data_example_result_all_mev['tendermint_rpc']['result']['data']['is_peered_with_sentinel'] = {
            'current': True,
            'previous': None
        }
        self.processed_data_example_result_all_mev['tendermint_rpc']['result']['meta_data']['is_mev_tendermint_node'] = True

        self.processed_data_example_result_options_None = copy.deepcopy(
            self.processed_data_example_result_all)
        self.processed_data_example_result_options_None['prometheus'][
            'result']['data']['voting_power']['current'] = None
        self.processed_data_example_result_options_None['tendermint_rpc'][
            'result']['data']['slashed']['current'] = {
            'slashed': False,
            'amount_map': {}
        }
        self.processed_data_example_result_options_None['tendermint_rpc'][
            'result']['data']['missed_blocks']['current'] = {
            'total_count': 0,
            'missed_heights': []
        }
        self.processed_data_example_result_options_None['tendermint_rpc'][
            'result']['data']['is_syncing']['current'] = None
        self.processed_data_example_result_options_None['cosmos_rest'][
            'result']['data']['bond_status']['current'] = None
        self.processed_data_example_result_options_None['cosmos_rest'][
            'result']['data']['jailed']['current'] = None
        self.processed_data_example_general_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            },
            'cosmos_rest': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            },
            'tendermint_rpc': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_mev_tendermint_node': False,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            }
        }
        self.processed_data_example_downtime_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                    'data': {
                        'went_down_at': {
                            'current': self.test_last_monitored,
                            'previous': None
                        }
                    }
                }
            },
            'cosmos_rest': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                    'data': {
                        'went_down_at': {
                            'current': self.test_last_monitored,
                            'previous': None
                        }
                    }
                }
            },
            'tendermint_rpc': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_1.node_name,
                        'node_id': self.node_1.node_id,
                        'node_parent_id': self.node_1.parent_id,
                        'time': self.test_last_monitored,
                        'is_mev_tendermint_node': False,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                    'data': {
                        'went_down_at': {
                            'current': self.test_last_monitored,
                            'previous': None
                        }
                    }
                }
            }
        }

        # Test transformer
        self.test_data_transformer = CosmosNodeDataTransformer(
            self.transformer_name, self.dummy_logger, self.redis, self.rabbitmq,
            self.max_queue_size)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_data_transformer.rabbitmq)
        delete_queue_if_exists(self.test_data_transformer.rabbitmq,
                               self.test_queue_name)
        delete_queue_if_exists(self.test_data_transformer.rabbitmq,
                               COSMOS_NODE_DT_INPUT_QUEUE_NAME)
        delete_exchange_if_exists(self.test_data_transformer.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_data_transformer.rabbitmq,
                                  RAW_DATA_EXCHANGE)
        delete_exchange_if_exists(self.test_data_transformer.rabbitmq,
                                  STORE_EXCHANGE)
        delete_exchange_if_exists(self.test_data_transformer.rabbitmq,
                                  ALERT_EXCHANGE)
        disconnect_from_rabbit(self.test_data_transformer.rabbitmq)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.redis = None
        self.node_1 = None
        self.test_state = None
        self.test_node_is_down_exception = None
        self.test_exception = None
        self.test_publishing_queue = None
        self.test_last_monitored = None
        self.test_heartbeat = None
        self.invalid_transformed_data = None
        self.test_data_transformer = None
        self.raw_data_example_result_all = None
        self.raw_data_example_result_options_None = None
        self.raw_data_example_general_error = None
        self.raw_data_example_downtime_error = None
        self.transformed_data_example_result_all = None
        self.transformed_data_example_result_options_None = None
        self.transformed_data_example_general_error = None
        self.transformed_data_example_downtime_error = None

    def test_str_returns_transformer_name(self) -> None:
        self.assertEqual(self.transformer_name, str(self.test_data_transformer))

    def test_transformer_name_returns_transformer_name(self) -> None:
        self.assertEqual(self.transformer_name,
                         self.test_data_transformer.transformer_name)

    def test_redis_returns_transformer_redis_instance(self) -> None:
        self.assertEqual(self.redis, self.test_data_transformer.redis)

    def test_state_returns_state(self) -> None:
        self.test_data_transformer._state = self.test_state
        self.assertEqual(self.test_state, self.test_data_transformer.state)

    def test_publishing_queue_returns_publishing_queue(self) -> None:
        self.test_data_transformer._publishing_queue = \
            self.test_publishing_queue
        self.assertEqual(self.test_publishing_queue,
                         self.test_data_transformer.publishing_queue)

    def test_publishing_queue_has_the_correct_max_size(self) -> None:
        self.assertEqual(self.max_queue_size,
                         self.test_data_transformer.publishing_queue.maxsize)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_data_transformer._listen_for_data()
        mock_start_consuming.assert_called_once()

    @mock.patch.object(RabbitMQApi, "basic_consume")
    @mock.patch.object(RabbitMQApi, "basic_qos")
    def test_initialise_rabbit_initializes_everything_as_expected(
            self, mock_basic_qos, mock_basic_consume) -> None:
        # To make sure that there is no connection/channel already established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges and queues have not already been
        # declared
        connect_to_rabbit(self.rabbitmq)
        self.test_data_transformer.rabbitmq.queue_delete(
            COSMOS_NODE_DT_INPUT_QUEUE_NAME)
        self.test_data_transformer.rabbitmq.exchange_delete(
            HEALTH_CHECK_EXCHANGE)
        self.test_data_transformer.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
        self.test_data_transformer.rabbitmq.exchange_delete(STORE_EXCHANGE)
        self.test_data_transformer.rabbitmq.exchange_delete(ALERT_EXCHANGE)
        self.rabbitmq.disconnect()

        self.test_data_transformer._initialise_rabbitmq()

        # Perform checks that the connection has been opened and marked as open,
        # that the delivery confirmation variable is set and basic_qos called
        # successfully.
        self.assertTrue(self.test_data_transformer.rabbitmq.is_connected)
        self.assertTrue(self.test_data_transformer.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_data_transformer.rabbitmq.channel._delivery_confirmation)
        mock_basic_qos.assert_called_once_with(
            prefetch_count=round(self.max_queue_size / 5))

        # Check whether the producing exchanges have been created by using
        # passive=True. If this check fails an exception is raised
        # automatically.
        self.test_data_transformer.rabbitmq.exchange_declare(STORE_EXCHANGE,
                                                             passive=True)
        self.test_data_transformer.rabbitmq.exchange_declare(ALERT_EXCHANGE,
                                                             passive=True)
        self.test_data_transformer.rabbitmq.exchange_declare(
            HEALTH_CHECK_EXCHANGE, passive=True)

        # Check whether the consuming exchanges and queues have been creating by
        # sending messages with the same routing keys as for the bindings.
        res = self.test_data_transformer.rabbitmq.queue_declare(
            COSMOS_NODE_DT_INPUT_QUEUE_NAME, False, True, False, False)
        self.assertEqual(0, res.method.message_count)
        self.test_data_transformer.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE,
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

        # Re-declare queue to get the number of messages
        res = self.test_data_transformer.rabbitmq.queue_declare(
            COSMOS_NODE_DT_INPUT_QUEUE_NAME, False, True, False, False)
        self.assertEqual(1, res.method.message_count)

        mock_basic_consume.assert_called_once()

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones set by send_heartbeat, and checks that the
        # heartbeat is received
        self.test_data_transformer._initialise_rabbitmq()

        # Delete the queue before to avoid messages in the queue on error.
        self.test_data_transformer.rabbitmq.queue_delete(self.test_queue_name)

        res = self.test_data_transformer.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_data_transformer.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)

        self.test_data_transformer._send_heartbeat(self.test_heartbeat)

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_data_transformer.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the HB
        _, _, body = self.test_data_transformer.rabbitmq.basic_get(
            self.test_queue_name)
        self.assertEqual(self.test_heartbeat, json.loads(body))

    def test_load_state_successful_if_node_exists_in_redis_and_redis_online(
            self) -> None:
        """
        We will perform this test both for when transformed data has been
        already stored in redis and for when default values have been stored in
        redis
        """

        # Test for when transformed data is stored in redis
        # Clean test db
        self.redis.delete_all()

        # Save state to Redis first
        save_cosmos_node_to_redis(self.redis, self.node_1)
        expected_loaded_node = copy.deepcopy(self.node_1)

        # Reset cosmos node to default values to detect the loading
        self.node_1.reset()

        # Load state
        loaded_cosmos_node = self.test_data_transformer.load_state(self.node_1)
        self.assertEqual(expected_loaded_node, loaded_cosmos_node)

        # Now for when default values are stored in redis. Note that at this
        # point node_1 has all the loaded metrics. This is important to confirm
        # that the data has changed to default
        self.redis.delete_all()

        # Store default data. We can assume that whenever default data is
        # loaded, the state is default also because loading occurs only when a
        # new state for a node is created.
        default_data_node = copy.deepcopy(self.node_1)
        default_data_node.reset()
        save_cosmos_node_to_redis(self.redis, default_data_node)

        self.node_1.reset()
        loaded_cosmos_node = self.test_data_transformer.load_state(self.node_1)
        self.assertEqual(default_data_node, loaded_cosmos_node)

        # Clean test db
        self.redis.delete_all()

    def test_load_state_keeps_same_state_if_node_in_redis_and_redis_offline(
            self) -> None:
        """
        We will perform this test both for when transformed data has been
        already stored in redis and for when default values have been stored in
        redis
        """
        # Set the _do_not_use_if_recently_went_down function to return True
        # as if redis is down
        self.test_data_transformer.redis._do_not_use_if_recently_went_down = \
            lambda: True

        # Test for when default values are stored in redis. Note that at this
        # point node_1 has all the loaded metrics. This is important to confirm
        # that the data has not changed to default
        self.redis.delete_all()

        # Store default data.
        default_data_node = copy.deepcopy(self.node_1)
        default_data_node.reset()
        save_cosmos_node_to_redis(self.redis, default_data_node)

        expected_loaded_node = copy.deepcopy(self.node_1)
        loaded_cosmos_node = self.test_data_transformer.load_state(self.node_1)
        self.assertEqual(expected_loaded_node, loaded_cosmos_node)

        # Test for when transformed data is stored in redis
        # Clean test db
        self.redis.delete_all()

        # Save state to Redis first
        save_cosmos_node_to_redis(self.redis, self.node_1)
        expected_loaded_node = copy.deepcopy(self.node_1)
        expected_loaded_node.reset()

        # Reset cosmos node to default values to check that the state was not
        # loaded
        self.node_1.reset()

        # Load state
        loaded_cosmos_node = self.test_data_transformer.load_state(self.node_1)
        self.assertEqual(expected_loaded_node, loaded_cosmos_node)

        # Clean test db
        self.redis.delete_all()

    def test_load_state_keeps_same_state_if_node_not_in_redis_and_redis_online(
            self) -> None:
        """
        We will perform this test both for when the current state has default
        entries, and for when it has transformed data
        """

        # Test for when the state contains transformed data
        # Clean test db
        self.redis.delete_all()

        # Load state
        expected_loaded_node = copy.deepcopy(self.node_1)
        loaded_cosmos_node = self.test_data_transformer.load_state(self.node_1)
        self.assertEqual(expected_loaded_node, loaded_cosmos_node)

        # Test for when the state contains default data
        # Clean test db
        self.redis.delete_all()
        self.node_1.reset()

        # Load state
        expected_loaded_node = copy.deepcopy(self.node_1)
        expected_loaded_node.reset()
        loaded_cosmos_node = self.test_data_transformer.load_state(self.node_1)
        self.assertEqual(expected_loaded_node, loaded_cosmos_node)

        # Clean test db
        self.redis.delete_all()

    def test_load_state_keeps_same_state_if_node_not_in_redis_and_redis_off(
            self) -> None:
        """
        We will perform this test both for when the current state has default
        entries, and for when it has transformed data
        """

        # Set the _do_not_use_if_recently_went_down function to return True
        # as if redis is down
        self.test_data_transformer.redis._do_not_use_if_recently_went_down = \
            lambda: True

        # Test for when the state contains transformed data
        # Clean test db
        self.redis.delete_all()

        # Load state
        expected_loaded_node = copy.deepcopy(self.node_1)
        loaded_cosmos_node = self.test_data_transformer.load_state(self.node_1)
        self.assertEqual(expected_loaded_node, loaded_cosmos_node)

        # Test for when the state contains default data
        # Clean test db
        self.redis.delete_all()
        self.node_1.reset()

        # Load state
        expected_loaded_node = copy.deepcopy(self.node_1)
        expected_loaded_node.reset()
        loaded_cosmos_node = self.test_data_transformer.load_state(self.node_1)
        self.assertEqual(expected_loaded_node, loaded_cosmos_node)

        # Clean test db
        self.redis.delete_all()

    @parameterized.expand([
        ({'prometheus': {}, 'cosmos_rest': {}, 'tendermint_rpc': {}},),
        ({'prometheus': 'bad_val', 'cosmos_rest': {}, 'tendermint_rpc': {}},),
        ({'cosmos_rest': 'bad_val', 'prometheus': {}, 'tendermint_rpc': {}},),
        ({'tendermint_rpc': 'bad_val', 'prometheus': {}, 'cosmos_rest': {}},),
        ({'bad_key': 'bad_val'},),
    ])
    def test_update_state_raises_unexpected_data_exception_if_unexpected_data(
            self, transformed_data) -> None:
        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_data_transformer._update_state,
                          transformed_data)

    def test_update_state_updates_state_correctly_if_result(self) -> None:
        expected_updated_node = copy.deepcopy(self.node_1)
        self.node_1.reset()
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        self.test_data_transformer._state['dummy_id'] = self.test_data_str
        old_state = copy.deepcopy(self.test_data_transformer._state)

        # Update state
        self.test_data_transformer._update_state(
            self.transformed_data_example_result_all)

        # Check that there are the same keys in the state
        self.assertEqual(old_state.keys(),
                         self.test_data_transformer.state.keys())

        # Check that the nodes not in question were not modified
        self.assertEqual(self.test_data_str,
                         self.test_data_transformer._state['dummy_id'])

        # Check that the nodes's state values have been modified correctly
        self.assertEqual(
            expected_updated_node,
            self.test_data_transformer._state[self.node_1.node_id])
        self.assertFalse(self.test_data_transformer._state[
                             self.node_1.node_id].is_down_tendermint_rpc)
        self.assertFalse(self.test_data_transformer._state[
                             self.node_1.node_id].is_down_cosmos_rest)
        self.assertFalse(self.test_data_transformer._state[
                             self.node_1.node_id].is_down_prometheus)

        # Update state with mev metrics
        self.test_data_transformer._update_state(
            self.transformed_data_example_result_mev)

        expected_updated_node.set_is_peered_with_sentinel(True)

        # Check that the nodes's state values have been modified correctly
        self.assertEqual(
            expected_updated_node,
            self.test_data_transformer._state[self.node_1.node_id])
        # Check that the nodes not in question were not modified
        self.assertEqual(self.test_data_str,
                         self.test_data_transformer._state['dummy_id'])
        # Check that setting state to false after true works
        self.transformed_data_example_result_mev['tendermint_rpc']['result']['data']['is_peered_with_sentinel'] = False
        self.test_data_transformer._update_state(
            self.transformed_data_example_result_mev)
        self.assertFalse(self.test_data_transformer._state[self.node_1.node_id].is_peered_with_sentinel)

    @parameterized.expand([
        ('self.transformed_data_example_general_error', False,),
        ('self.transformed_data_example_downtime_error', True,)
    ])
    def test_update_state_updates_state_correctly_if_error(
            self, transformed_data_err, is_downtime_error) -> None:
        transformed_data_eval = eval(transformed_data_err)
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        self.test_data_transformer._state['dummy_id'] = self.test_data_str
        old_state = copy.deepcopy(self.test_data_transformer._state)

        self.test_data_transformer._update_state(transformed_data_eval)

        # Check that there are the same keys in the state
        self.assertEqual(old_state.keys(),
                         self.test_data_transformer.state.keys())

        # Check that the nodes not in question are not modified
        self.assertEqual(self.test_data_str,
                         self.test_data_transformer._state['dummy_id'])

        old_modified_node_state = old_state[self.node_1.node_id]
        if is_downtime_error:
            self.assertTrue(
                self.test_data_transformer._state[
                    self.node_1.node_id].is_down_prometheus)
            self.assertTrue(
                self.test_data_transformer._state[
                    self.node_1.node_id].is_down_cosmos_rest)
            self.assertTrue(
                self.test_data_transformer._state[
                    self.node_1.node_id].is_down_tendermint_rpc)
            old_modified_node_state.set_prometheus_as_down(
                transformed_data_eval['prometheus']['error']['data'][
                    'went_down_at'])
            old_modified_node_state.set_cosmos_rest_as_down(
                transformed_data_eval['cosmos_rest']['error']['data'][
                    'went_down_at'])
            old_modified_node_state.set_tendermint_rpc_as_down(
                transformed_data_eval['tendermint_rpc']['error']['data'][
                    'went_down_at'])
        else:
            self.assertFalse(
                self.test_data_transformer._state[
                    self.node_1.node_id].is_down_prometheus)
            self.assertFalse(
                self.test_data_transformer._state[
                    self.node_1.node_id].is_down_cosmos_rest)
            self.assertFalse(
                self.test_data_transformer._state[
                    self.node_1.node_id].is_down_tendermint_rpc)

        self.assertEqual(
            old_modified_node_state,
            self.test_data_transformer.state[self.node_1.node_id])

    @parameterized.expand([
        ('self.transformed_data_example_result_all',),
        ('self.transformed_data_example_result_options_None',),
        ('self.transformed_data_example_general_error',),
        ('self.transformed_data_example_downtime_error',)
    ])
    def test_process_transformed_data_for_saving_returns_expected_data(
            self, transformed_data: str) -> None:
        transformed_data_eval = eval(transformed_data)
        processed_data = \
            self.test_data_transformer._process_transformed_data_for_saving(
                transformed_data_eval)
        self.assertDictEqual(transformed_data_eval, processed_data)

    @parameterized.expand([
        ({'prometheus': {}, 'cosmos_rest': {}, 'tendermint_rpc': {}},),
        ({'prometheus': 'bad_val', 'cosmos_rest': {}, 'tendermint_rpc': {}},),
        ({'cosmos_rest': 'bad_val', 'prometheus': {}, 'tendermint_rpc': {}},),
        ({'tendermint_rpc': 'bad_val', 'prometheus': {}, 'cosmos_rest': {}},),
        ({'bad_key': 'bad_val'},),
    ])
    def test_proc_trans_data_for_saving_raises_unexp_data_except_on_unexp_data(
            self, transformed_data) -> None:
        self.assertRaises(
            ReceivedUnexpectedDataException,
            self.test_data_transformer._process_transformed_data_for_saving,
            transformed_data)

    @parameterized.expand([
        ('self.transformed_data_example_result_all',
         'self.processed_data_example_result_all'),
        ('self.transformed_data_example_result_options_None',
         'self.processed_data_example_result_options_None'),
        ('self.transformed_data_example_general_error',
         'self.processed_data_example_general_error'),
        ('self.transformed_data_example_downtime_error',
         'self.processed_data_example_downtime_error'),
        ('self.transformed_data_example_result_mev',
         'self.processed_data_example_result_all_mev'),
    ])
    def test_process_transformed_data_for_alerting_returns_expected_data(
            self, transformed_data: str, expected_processed_data: str) -> None:
        self.node_1.reset()
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        actual_data = \
            self.test_data_transformer._process_transformed_data_for_alerting(
                eval(transformed_data))
        self.assertEqual(eval(expected_processed_data), actual_data)

    @parameterized.expand([
        ({'prometheus': {}, 'cosmos_rest': {}, 'tendermint_rpc': {}},),
        ({'prometheus': 'bad_val', 'cosmos_rest': {}, 'tendermint_rpc': {}},),
        ({'cosmos_rest': 'bad_val', 'prometheus': {}, 'tendermint_rpc': {}},),
        ({'tendermint_rpc': 'bad_val', 'prometheus': {}, 'cosmos_rest': {}},),
        ({'bad_key': 'bad_val'},),
    ])
    def test_proc_trans_data_for_alerting_raise_unex_data_except_on_unex_data(
            self, transformed_data) -> None:
        self.assertRaises(
            ReceivedUnexpectedDataException,
            self.test_data_transformer._process_transformed_data_for_alerting,
            transformed_data)

    @parameterized.expand([
        ('self.raw_data_example_general_error',
         'self.transformed_data_example_general_error',),
        ('self.raw_data_example_downtime_error',
         'self.transformed_data_example_downtime_error',),
        ('self.raw_data_example_result_all',
         'self.transformed_data_example_result_all',),
        ('self.raw_data_example_result_options_None',
         'self.transformed_data_example_result_options_None',),
    ])
    @mock.patch.object(CosmosNodeDataTransformer,
                       "_process_transformed_data_for_alerting")
    @mock.patch.object(CosmosNodeDataTransformer,
                       "_process_transformed_data_for_saving")
    def test_transform_data_returns_expected_data(
            self, raw_data, expected_transformed_data, mock_proc_saving,
            mock_proc_alerting) -> None:
        self.node_1.reset()
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        proc_saving_return = {'key_1': 'val1'}
        proc_alerting_return = {'key_2': 'val2'}
        mock_proc_saving.return_value = proc_saving_return
        mock_proc_alerting.return_value = proc_alerting_return

        trans_data, data_for_alerting, data_for_saving = \
            self.test_data_transformer._transform_data(eval(raw_data))

        self.assertEqual(eval(expected_transformed_data), trans_data)
        self.assertEqual(proc_alerting_return, data_for_alerting)
        self.assertEqual(proc_saving_return, data_for_saving)

    @parameterized.expand([
        ({'prometheus': {}, 'cosmos_rest': {}, 'tendermint_rpc': {}},),
        ({'prometheus': 'bad_val', 'cosmos_rest': {}, 'tendermint_rpc': {}},),
        ({'cosmos_rest': 'bad_val', 'prometheus': {}, 'tendermint_rpc': {}},),
        ({'tendermint_rpc': 'bad_val', 'prometheus': {}, 'cosmos_rest': {}},),
        ({'bad_key': 'bad_val'},),
    ])
    def test_transform_data_raises_unexpected_data_exception_on_unexpected_data(
            self, raw_data) -> None:
        self.assertRaises(
            ReceivedUnexpectedDataException,
            self.test_data_transformer._transform_data, raw_data)

    @parameterized.expand([
        ('self.processed_data_example_general_error',
         'self.transformed_data_example_general_error'),
        ('self.processed_data_example_downtime_error',
         'self.transformed_data_example_downtime_error'),
        ('self.processed_data_example_result_all',
         'self.transformed_data_example_result_all'),
        ('self.processed_data_example_result_options_None',
         'self.transformed_data_example_result_options_None'),
    ])
    def test_place_latest_data_on_queue_places_the_correct_data_on_queue(
            self, data_for_alerting: str, data_for_saving: str) -> None:
        self.test_data_transformer._place_latest_data_on_queue(
            eval(data_for_alerting), eval(data_for_saving)
        )
        expected_data_for_alerting = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            'data': eval(data_for_alerting),
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        expected_data_for_saving = {
            'exchange': STORE_EXCHANGE,
            'routing_key': COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            'data': eval(data_for_saving),
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }

        self.assertEqual(
            2, self.test_data_transformer.publishing_queue.qsize())
        self.assertDictEqual(
            expected_data_for_alerting,
            self.test_data_transformer.publishing_queue.queue[0])
        self.assertDictEqual(
            expected_data_for_saving,
            self.test_data_transformer.publishing_queue.queue[1])

    @parameterized.expand([
        ({
             'prometheus': {
                 'result': {
                     'meta_data': {
                         'node_parent_id': 'node_parent_id1',
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             },
             'cosmos_rest': {
                 'result': {
                     'meta_data': {
                         'node_parent_id': 'node_parent_id1',
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             },
             'tendermint_rpc': {
                 'error': {
                     'meta_data': {
                         'node_parent_id': 'node_parent_id1',
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             }
         }, ('node_parent_id1', 'node_id1', 'node_name1',),),
        ({
             'prometheus': {
                 'error': {
                     'meta_data': {
                         'node_parent_id': 'node_parent_id1',
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             }
         }, None,),
        ({'prometheus': {}, 'cosmos_rest': {}, 'tendermint_rpc': {}}, None,),
        ({
             'prometheus': {
                 'bad_index': {
                     'meta_data': {
                         'node_parent_id': 'node_parent_id1',
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             },
             'cosmos_rest': {
                 'error': {
                     'meta_data': {
                         'node_parent_id': 'node_parent_id1',
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             },
             'tendermint_rpc': {
                 'result': {
                     'meta_data': {
                         'node_parent_id': 'node_parent_id1',
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             }
         }, None,),
        ({
             'prometheus': {
                 'result': {
                     'meta_data': {
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             },
             'cosmos_rest': {
                 'error': {
                     'meta_data': {
                         'node_parent_id': 'node_parent_id1',
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             },
             'tendermint_rpc': {
                 'result': {
                     'meta_data': {
                         'node_parent_id': 'node_parent_id1',
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             }
         }, None,),
        ({
             'prometheus': {
                 'result': {
                     'meta_data': {
                         'node_parent_id': 'bad_id',
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             },
             'cosmos_rest': {
                 'error': {
                     'meta_data': {
                         'node_parent_id': 'node_parent_id1',
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             },
             'tendermint_rpc': {
                 'result': {
                     'meta_data': {
                         'node_parent_id': 'node_parent_id1',
                         'node_id': 'node_id1',
                         'node_name': 'node_name1',
                     }
                 }
             }
         }, None,),
    ])
    def test_validate_and_parse_raw_data_sources_return(
            self, raw_data, expected_ret) -> None:
        if expected_ret:
            actual_ret = (
                self.test_data_transformer._validate_and_parse_raw_data_sources(
                    raw_data)
            )
            self.assertEqual(expected_ret, actual_ret)
        else:
            self.assertRaises(
                ReceivedUnexpectedDataException,
                self.test_data_transformer._validate_and_parse_raw_data_sources,
                raw_data)

    @parameterized.expand([({}, False,), ('self.test_state', True), ])
    @mock.patch.object(CosmosNodeDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_transforms_data_if_data_has_correct_structure(
            self, state, state_is_str: bool, mock_ack, mock_trans_data) -> None:
        # We will check that the data is transformed by checking that
        # `_transform_data` is called correctly. Note that both the validation
        # and the transformations were tested in previous tests. Also we will
        # test for both result and error, and for when the node is both in the
        # state and not in the state.
        mock_ack.return_value = None
        mock_trans_data.return_value = (None, None, None)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        body_result = json.dumps(self.raw_data_example_result_all)
        body_error = json.dumps(self.raw_data_example_general_error)
        properties = pika.spec.BasicProperties()

        if state_is_str:
            self.test_data_transformer._state = copy.deepcopy(eval(state))
        else:
            self.test_data_transformer._state = copy.deepcopy(state)

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties,
                                                     body_result)
        mock_trans_data.assert_called_once_with(
            self.raw_data_example_result_all)

        # To reset the state as if the node was not already added
        if state_is_str:
            self.test_data_transformer._state = copy.deepcopy(eval(state))
        else:
            self.test_data_transformer._state = copy.deepcopy(state)

        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties,
                                                     body_error)

        self.assertEqual(2, mock_trans_data.call_count)
        args, _ = mock_trans_data.call_args
        self.assertEqual(self.raw_data_example_general_error, args[0])
        self.assertEqual(1, len(args))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @parameterized.expand([
        (ReceivedUnexpectedDataException,),
        (KeyError,),
        (Exception,),
    ])
    @mock.patch.object(CosmosNodeDataTransformer,
                       "_validate_and_parse_raw_data_sources")
    @mock.patch.object(CosmosNodeDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_proc_raw_data_does_not_call_trans_data_if_validate_raise_exception(
            self, exception, mock_ack, mock_trans_data,
            mock_validation) -> None:
        mock_ack.return_value = None
        mock_trans_data.return_value = None
        mock_validation.side_effect = exception

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_all)
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties,
                                                     body)

        mock_trans_data.assert_not_called()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all',
         'self.transformed_data_example_result_all',),
        ('self.raw_data_example_result_mev',
          'self.transformed_data_example_result_mev',),
        ('self.raw_data_example_result_options_None',
         'self.transformed_data_example_result_options_None'),
        ('self.raw_data_example_general_error',
         'self.transformed_data_example_general_error',),
        ('self.raw_data_example_downtime_error',
         'self.transformed_data_example_downtime_error',),
    ])
    @mock.patch.object(CosmosNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_updates_state_if_no_processing_errors(
            self, raw_data, transformed_data, mock_ack,
            mock_update_state) -> None:
        self.node_1.reset()
        mock_ack.return_value = None
        mock_update_state.return_value = None
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        mock_update_state.assert_called_once_with(eval(transformed_data))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all', Exception('test'), None,),
        ('self.raw_data_example_result_options_None', Exception('test'), None,),
        ('self.raw_data_example_general_error', Exception('test'), None,),
        ('self.raw_data_example_downtime_error', Exception('test'), None,),
        ('self.raw_data_example_result_all', None, Exception('test'),),
        ('self.raw_data_example_result_options_None', None, Exception('test'),),
        ('self.raw_data_example_general_error', None, Exception('test'),),
        ('self.raw_data_example_downtime_error', None, Exception('test'),),
    ])
    @mock.patch.object(CosmosNodeDataTransformer,
                       "_validate_and_parse_raw_data_sources")
    @mock.patch.object(CosmosNodeDataTransformer, "_transform_data")
    @mock.patch.object(CosmosNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_update_state_if_processing_errors(
            self, raw_data, validation_exception, transformation_exception,
            mock_ack, mock_update_state, mock_transform, mock_validate) -> None:
        # We will test this for both when the raw_data structure is invalid and
        # when the transformation encounters a problem
        mock_ack.return_value = None
        mock_update_state.return_value = None
        if validation_exception:
            mock_validate.side_effect = validation_exception
        else:
            mock_validate.return_value = (True,
                                          self.node_1.parent_id,
                                          self.node_1.node_id,
                                          self.node_1.node_name,)
        if transformation_exception:
            mock_transform.side_effect = transformation_exception
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        mock_update_state.assert_not_called()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all',
         'self.transformed_data_example_result_all',
         'self.processed_data_example_result_all',),
        ('self.raw_data_example_result_options_None',
         'self.transformed_data_example_result_options_None',
         'self.processed_data_example_result_options_None',),
        ('self.raw_data_example_general_error',
         'self.transformed_data_example_general_error',
         'self.processed_data_example_general_error',),
        ('self.raw_data_example_downtime_error',
         'self.transformed_data_example_downtime_error',
         'self.processed_data_example_downtime_error',),
    ])
    @mock.patch.object(CosmosNodeDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(CosmosNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_places_data_on_queue_if_no_processing_errors(
            self, raw_data, transformed_data, processed_data, mock_ack,
            mock_update_state, mock_place_on_queue) -> None:
        mock_ack.return_value = None
        mock_update_state.return_value = None
        mock_place_on_queue.return_value = None
        self.node_1.reset()
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        mock_place_on_queue.assert_called_once_with(eval(processed_data),
                                                    eval(transformed_data))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all', Exception('test'), None, None,),
        ('self.raw_data_example_result_all', None, Exception('test'), None,),
        ('self.raw_data_example_result_all', None, None, Exception('test'),),
        ('self.raw_data_example_result_options_None', Exception('test'), None,
         None,),
        ('self.raw_data_example_result_options_None', None, Exception('test'),
         None,),
        ('self.raw_data_example_result_options_None', None, None,
         Exception('test'),),
        ('self.raw_data_example_general_error', Exception('test'), None, None,),
        ('self.raw_data_example_general_error', None, Exception('test'), None,),
        ('self.raw_data_example_general_error', None, None, Exception('test'),),
        ('self.raw_data_example_downtime_error', Exception('test'), None,
         None,),
        ('self.raw_data_example_downtime_error', None, Exception('test'),
         None,),
        ('self.raw_data_example_downtime_error', None, None,
         Exception('test'),),
    ])
    @mock.patch.object(CosmosNodeDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(CosmosNodeDataTransformer,
                       "_validate_and_parse_raw_data_sources")
    @mock.patch.object(CosmosNodeDataTransformer, "_transform_data")
    @mock.patch.object(CosmosNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_place_data_on_queue_if_processing_errors(
            self, raw_data, validation_exception, transformation_exception,
            update_exception, mock_ack, mock_update_state, mock_transform,
            mock_validate, mock_place_on_queue) -> None:
        # We will test this for whenever a processing error happens in either
        # stages of the transformation process.
        mock_ack.return_value = None
        mock_place_on_queue.return_value = None
        if validation_exception:
            mock_validate.side_effect = validation_exception
        else:
            mock_validate.return_value = (True,
                                          self.node_1.parent_id,
                                          self.node_1.node_id,
                                          self.node_1.node_name)
        if update_exception:
            mock_update_state.side_effect = update_exception
        else:
            mock_update_state.return_value = None
        if transformation_exception:
            mock_transform.side_effect = transformation_exception
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        mock_place_on_queue.assert_not_called()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all',),
        ('self.raw_data_example_result_options_None',),
        ('self.raw_data_example_general_error',),
        ('self.raw_data_example_downtime_error',),
    ])
    @mock.patch.object(CosmosNodeDataTransformer, "_send_data")
    @mock.patch.object(CosmosNodeDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(CosmosNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_data_in_queue_if_no_processing_errors(
            self, raw_data, mock_ack, mock_update_state, mock_place_on_queue,
            mock_send_data) -> None:
        mock_ack.return_value = None
        mock_update_state.return_value = None
        mock_place_on_queue.return_value = None
        mock_send_data.return_value = None
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        mock_send_data.assert_called_once()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all', Exception('test'), None, None,),
        ('self.raw_data_example_result_all', None, Exception('test'), None,),
        ('self.raw_data_example_result_all', None, None, Exception('test'),),
        ('self.raw_data_example_result_options_None', Exception('test'), None,
         None,),
        ('self.raw_data_example_result_options_None', None, Exception('test'),
         None,),
        ('self.raw_data_example_result_options_None', None, None,
         Exception('test'),),
        ('self.raw_data_example_general_error', Exception('test'), None, None,),
        ('self.raw_data_example_general_error', None, Exception('test'), None,),
        ('self.raw_data_example_general_error', None, None, Exception('test'),),
        ('self.raw_data_example_downtime_error', Exception('test'), None,
         None,),
        ('self.raw_data_example_downtime_error', None, Exception('test'),
         None,),
        ('self.raw_data_example_downtime_error', None, None,
         Exception('test'),),
    ])
    @mock.patch.object(CosmosNodeDataTransformer, "_send_data")
    @mock.patch.object(CosmosNodeDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(CosmosNodeDataTransformer,
                       "_validate_and_parse_raw_data_sources")
    @mock.patch.object(CosmosNodeDataTransformer, "_transform_data")
    @mock.patch.object(CosmosNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_data_in_queue_if_processing_errors(
            self, raw_data, validation_exception, transformation_exception,
            update_exception, mock_ack, mock_update_state, mock_transform,
            mock_validate, mock_place_on_queue, mock_send_data) -> None:
        # We will test this for whenever a processing error happens in either
        # stages of the transformation process.
        mock_ack.return_value = None
        mock_place_on_queue.return_value = None
        mock_send_data.return_value = None
        if validation_exception:
            mock_validate.side_effect = validation_exception
        else:
            mock_validate.return_value = (True,
                                          self.node_1.parent_id,
                                          self.node_1.node_id,
                                          self.node_1.node_name)
        if update_exception:
            mock_update_state.side_effect = update_exception
        else:
            mock_update_state.return_value = None
        if transformation_exception:
            mock_transform.side_effect = transformation_exception
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        mock_send_data.assert_called_once_with()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all',),
        ('self.raw_data_example_result_options_None',),
        ('self.raw_data_example_general_error',),
        ('self.raw_data_example_downtime_error',),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(CosmosNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(CosmosNodeDataTransformer, "_send_data")
    @mock.patch.object(CosmosNodeDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(CosmosNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_hb_if_no_proc_errors_and_send_data_success(
            self, raw_data, mock_ack, mock_update_state, mock_place_on_queue,
            mock_send_data, mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_update_state.return_value = None
        mock_place_on_queue.return_value = None
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        test_heartbeat = {
            'component_name': self.transformer_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        mock_send_hb.assert_called_with(test_heartbeat)

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all', Exception('test'), None, None,
         None,),
        ('self.raw_data_example_result_all', None, Exception('test'), None,
         None,),
        ('self.raw_data_example_result_all', None, None, Exception('test'),
         None,),
        ('self.raw_data_example_result_all', None, None, None,
         Exception('test'),),
        ('self.raw_data_example_result_options_None', Exception('test'), None,
         None, None,),
        ('self.raw_data_example_result_options_None', None, Exception('test'),
         None, None,),
        ('self.raw_data_example_result_options_None', None, None,
         Exception('test'), None,),
        ('self.raw_data_example_result_options_None', None, None,
         None, Exception('test'),),
        ('self.raw_data_example_general_error', Exception('test'), None,
         None, None,),
        ('self.raw_data_example_general_error', None, Exception('test'),
         None, None,),
        ('self.raw_data_example_general_error', None, None, Exception('test'),
         None,),
        ('self.raw_data_example_general_error', None, None, None,
         Exception('test'),),
        ('self.raw_data_example_downtime_error', Exception('test'), None,
         None, None,),
        ('self.raw_data_example_downtime_error', None, Exception('test'),
         None, None,),
        ('self.raw_data_example_downtime_error', None, None,
         Exception('test'), None,),
        ('self.raw_data_example_downtime_error', None, None,
         None, Exception('test'),),
    ])
    @mock.patch.object(CosmosNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(CosmosNodeDataTransformer, "_send_data")
    @mock.patch.object(CosmosNodeDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(CosmosNodeDataTransformer,
                       "_validate_and_parse_raw_data_sources")
    @mock.patch.object(CosmosNodeDataTransformer, "_transform_data")
    @mock.patch.object(CosmosNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_send_hb_if_processing_errors(
            self, raw_data, validation_exception, transformation_exception,
            update_exception, send_data_exception, mock_ack, mock_update_state,
            mock_transform, mock_validate, mock_place_on_queue, mock_send_data,
            mock_send_heartbeat) -> None:
        # We will test this for whenever a processing error happens in either
        # stages of the transformation process.
        mock_ack.return_value = None
        mock_place_on_queue.return_value = None
        mock_send_heartbeat.return_value = None
        if validation_exception:
            mock_validate.side_effect = validation_exception
        else:
            mock_validate.return_value = (True,
                                          self.node_1.parent_id,
                                          self.node_1.node_id,
                                          self.node_1.node_name)
        if update_exception:
            mock_update_state.side_effect = update_exception
        else:
            mock_update_state.return_value = None
        if transformation_exception:
            mock_transform.side_effect = transformation_exception
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        if send_data_exception:
            mock_send_data.side_effect = send_data_exception
            self.assertRaises(Exception,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body)
        else:
            mock_send_data.return_value = None
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body)

        mock_send_heartbeat.assert_not_called()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        (MessageWasNotDeliveredException('test'), None,),
        (None, MessageWasNotDeliveredException('test'),),
    ])
    @mock.patch.object(CosmosNodeDataTransformer, "_send_data")
    @mock.patch.object(CosmosNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_raise_msg_not_del_exce_if_raised(
            self, send_data_exception, send_hb_exception, mock_ack,
            mock_send_hb, mock_send_data) -> None:
        # We will perform this test for both when the exception is raised by
        # send_data and by send_heartbeat
        if send_data_exception:
            mock_send_data.side_effect = send_data_exception
        else:
            mock_send_data.return_value = None

        if send_hb_exception:
            mock_send_hb.side_effect = send_hb_exception
        else:
            mock_send_hb.return_value = None

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_all)
        properties = pika.spec.BasicProperties()

        try:
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body)
        except MessageWasNotDeliveredException as e:
            self.fail("Was not expecting {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        (AMQPConnectionError('test'), None, AMQPConnectionError,),
        (None, AMQPConnectionError('test'), AMQPConnectionError),
        (AMQPChannelError('test'), None, AMQPChannelError),
        (None, AMQPChannelError('test'), AMQPChannelError),
        (Exception('test'), None, Exception,),
        (None, Exception('test'), Exception,),
    ])
    @mock.patch.object(CosmosNodeDataTransformer, "_send_data")
    @mock.patch.object(CosmosNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_raises_unexpected_errors_if_raised(
            self, send_data_exception, send_hb_exception, exception_instance,
            mock_ack, mock_send_hb, mock_send_data) -> None:
        # We will perform this test for both when the exception is raised by
        # send_data and by send_heartbeat
        if send_data_exception:
            mock_send_data.side_effect = send_data_exception
        else:
            mock_send_data.return_value = None

        if send_hb_exception:
            mock_send_hb.side_effect = send_hb_exception
        else:
            mock_send_hb.return_value = None

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_all)
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_instance,
                          self.test_data_transformer._process_raw_data,
                          blocking_channel, method, properties, body)

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()
