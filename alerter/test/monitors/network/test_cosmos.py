import json
import logging
import unittest
from datetime import timedelta, datetime
from unittest import mock

from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.api_wrappers.cosmos import CosmosRestServerApiWrapper
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.network.cosmos import CosmosNetworkMonitor
from src.utils import env
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, RAW_DATA_EXCHANGE,
    COSMOS_NETWORK_RAW_DATA_ROUTING_KEY)
from src.utils.exceptions import PANICException, MessageWasNotDeliveredException
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, delete_exchange_if_exists,
    disconnect_from_rabbit)
from test.utils.cosmos.cosmos import CosmosTestNodes

# Retrieved data/metrics and their mocks
retrieved_proposals_1_v1 = {
    'height': "999",
    'result': [
        {
            'id': '1',
            'content': {
                'type': '/cosmos.gov.v1beta1.TextProposal',
                'value': {
                    'title': 'Test Proposal Title',
                    'description': 'Test Proposal Description'
                }
            },
            'status': 3,
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        }
    ]
}

retrieved_proposals_1_v2 = {
    'height': "999",
    'result': [
        {
            'id': '1',
            'content': {
                'type': '/cosmos.gov.v1beta1.TextProposal',
                'value': {
                    'title': 'Test Proposal Title',
                    'description': 'Test Proposal Description'
                }
            },
            'proposal_status': 'Passed',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        }
    ]
}

retrieved_proposals_1_v3 = {
    'proposals': [
        {
            'proposal_id': '1',
            'content': {
                'type': '/cosmos.gov.v1beta1.TextProposal',
                'value': {
                    'title': 'Test Proposal Title',
                    'description': 'Test Proposal Description'
                }
            },
            'status': 'proposal_status_passed',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        }
    ],
    'pagination': {
        'next_key': None,
        'total': '1'
    }
}

retrieved_proposals_1_v4 = {
    'proposals': [
        {
            'proposal_id': '1',
            'content': {
                'type': '/cosmos.gov.v1beta1.TextProposal',
                'title': 'Test Proposal Title',
                'description': 'Test Proposal Description'
            },
            'status': 'passed',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        }
    ],
    'pagination': {
        'next_key': None,
        'total': '1'
    }
}

retrieved_proposals_2_v1 = {
    'height': "999",
    'result': [
        {
            'id': '1',
            'content': {
                'type': '/cosmos.gov.v1beta1.TextProposal',
                'value': {
                    'title': 'Test Proposal Title',
                    'description': 'Test Proposal Description'
                }
            },
            'status': 4,
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        },
        {
            'proposal_id': '2',
            'content': {
                'type': '/cosmos.gov.v1beta1.TextProposal',
                'value': {
                    'title': 'Test Proposal Title 2',
                    'description': 'Test Proposal Description 2'
                }
            },
            'status': 2,
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        }
    ]
}

retrieved_proposals_2_v2 = {
    'height': "999",
    'result': [
        {
            'id': '1',
            'content': {
                'type': '/cosmos.gov.v1beta1.TextProposal',
                'value': {
                    'title': 'Test Proposal Title',
                    'description': 'Test Proposal Description'
                }
            },
            'proposal_status': 'Rejected',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        },
        {
            'proposal_id': '2',
            'content': {
                'type': '/cosmos.gov.v1beta1.TextProposal',
                'value': {
                    'title': 'Test Proposal Title 2',
                    'description': 'Test Proposal Description 2'
                }
            },
            'proposal_status': 'Voting_Period',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        }
    ]
}

retrieved_proposals_2_v3 = {
    'proposals': [
        {
            'proposal_id': '1',
            'content': {
                'type': '/cosmos.gov.v1beta1.TextProposal',
                'title': 'Test Proposal Title',
                'description': 'Test Proposal Description'
            },
            'status': 'PROPOSAL_STATUS_REJECTED',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        },
        {
            'proposal_id': '2',
            'content': {
                'type': '/cosmos.gov.v1beta1.TextProposal',
                'value': {
                    'title': 'Test Proposal Title 2',
                    'description': 'Test Proposal Description 2'
                }
            },
            'status': 'PROPOSAL_STATUS_VOTING_PERIOD',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        }
    ],
    'pagination': {
        'next_key': None,
        'total': '2'
    }
}

retrieved_proposals_2_v4 = {
    'proposals': [
        {
            'proposal_id': '1',
            'content': {
                'type': '/cosmos.gov.v1beta1.TextProposal',
                'title': 'Test Proposal Title',
                'description': 'Test Proposal Description'
            },
            'status': 'rejected',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        },
        {
            'proposal_id': '2',
            'content': {
                'type': '/cosmos.gov.v1beta1.TextProposal',
                'value': {
                    'title': 'Test Proposal Title 2',
                    'description': 'Test Proposal Description 2'
                }
            },
            'status': 'voting_period',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        }
    ],
    'pagination': {
        'next_key': None,
        'total': '2'
    }
}

retrieved_proposals_3_v1 = [
    {
        'proposals': [
            {
                'proposal_id': '1',
                'content': {
                    'type': '/cosmos.gov.v1beta1.TextProposal',
                    'title': 'Test Proposal Title',
                    'description': 'Test Proposal Description'
                },
                'status': 'PROPOSAL_STATUS_REJECTED',
                'final_tally_result': {
                    'yes': '100',
                    'abstain': '100',
                    'no': '100',
                    'no_with_veto': '100'
                },
                'submit_time': '2019-03-20T06:41:27.040075748Z',
                'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
                'total_deposit': [
                    {
                        'denom': 'uatom',
                        'amount': '512100000'
                    }
                ],
                'voting_start_time': '2019-03-20T20:43:59.630492307Z',
                'voting_end_time': '2019-04-03T20:43:59.630492307Z'
            }
        ],
        'pagination': {
            'next_key': 'test_key_1',
            'total': '1'
        }
    },
    {
        'proposals': [
            {
                'proposal_id': '2',
                'content': {
                    'type': '/cosmos.gov.v1beta1.TextProposal',
                    'value': {
                        'title': 'Test Proposal Title 2',
                        'description': 'Test Proposal Description 2'
                    }
                },
                'status': 'PROPOSAL_STATUS_VOTING_PERIOD',
                'final_tally_result': {
                    'yes': '100',
                    'abstain': '100',
                    'no': '100',
                    'no_with_veto': '100'
                },
                'submit_time': '2019-03-20T06:41:27.040075748Z',
                'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
                'total_deposit': [
                    {
                        'denom': 'uatom',
                        'amount': '512100000'
                    }
                ],
                'voting_start_time': '2019-03-20T20:43:59.630492307Z',
                'voting_end_time': '2019-04-03T20:43:59.630492307Z'
            }
        ],
        'pagination': {
            'next_key': 'test_key_2',
            'total': '1'
        }
    },
    {
        'proposals': [
            {
                'proposal_id': '3',
                'content': {
                    'type': '/cosmos.gov.v1beta1.TextProposal',
                    'value': {
                        'title': 'Test Proposal Title 3',
                        'description': 'Test Proposal Description 3'
                    }
                },
                'status': 'PROPOSAL_STATUS_DEPOSIT_PERIOD',
                'final_tally_result': {
                    'yes': '100',
                    'abstain': '100',
                    'no': '100',
                    'no_with_veto': '100'
                },
                'submit_time': '2019-03-20T06:41:27.040075748Z',
                'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
                'total_deposit': [
                    {
                        'denom': 'uatom',
                        'amount': '512100000'
                    }
                ],
                'voting_start_time': '2019-03-20T20:43:59.630492307Z',
                'voting_end_time': '2019-04-03T20:43:59.630492307Z'
            }
        ],
        'pagination': {
            'next_key': None,
            'total': '1'
        }
    }
]

retrieved_proposals_3_v2 = [
    {
        'proposals': [
            {
                'proposal_id': '1',
                'content': {
                    'type': '/cosmos.gov.v1beta1.TextProposal',
                    'title': 'Test Proposal Title',
                    'description': 'Test Proposal Description'
                },
                'status': 'rejected',
                'final_tally_result': {
                    'yes': '100',
                    'abstain': '100',
                    'no': '100',
                    'no_with_veto': '100'
                },
                'submit_time': '2019-03-20T06:41:27.040075748Z',
                'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
                'total_deposit': [
                    {
                        'denom': 'uatom',
                        'amount': '512100000'
                    }
                ],
                'voting_start_time': '2019-03-20T20:43:59.630492307Z',
                'voting_end_time': '2019-04-03T20:43:59.630492307Z'
            }
        ],
        'pagination': {
            'next_key': 'test_key_1',
            'total': '1'
        }
    },
    {
        'proposals': [
            {
                'proposal_id': '2',
                'content': {
                    'type': '/cosmos.gov.v1beta1.TextProposal',
                    'value': {
                        'title': 'Test Proposal Title 2',
                        'description': 'Test Proposal Description 2'
                    }
                },
                'status': 'voting_period',
                'final_tally_result': {
                    'yes': '100',
                    'abstain': '100',
                    'no': '100',
                    'no_with_veto': '100'
                },
                'submit_time': '2019-03-20T06:41:27.040075748Z',
                'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
                'total_deposit': [
                    {
                        'denom': 'uatom',
                        'amount': '512100000'
                    }
                ],
                'voting_start_time': '2019-03-20T20:43:59.630492307Z',
                'voting_end_time': '2019-04-03T20:43:59.630492307Z'
            }
        ],
        'pagination': {
            'next_key': 'test_key_2',
            'total': '1'
        }
    },
    {
        'proposals': [
            {
                'proposal_id': '3',
                'content': {
                    'type': '/cosmos.gov.v1beta1.TextProposal',
                    'value': {
                        'title': 'Test Proposal Title 3',
                        'description': 'Test Proposal Description 3'
                    }
                },
                'status': 'deposit_period',
                'final_tally_result': {
                    'yes': '100',
                    'abstain': '100',
                    'no': '100',
                    'no_with_veto': '100'
                },
                'submit_time': '2019-03-20T06:41:27.040075748Z',
                'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
                'total_deposit': [
                    {
                        'denom': 'uatom',
                        'amount': '512100000'
                    }
                ],
                'voting_start_time': '2019-03-20T20:43:59.630492307Z',
                'voting_end_time': '2019-04-03T20:43:59.630492307Z'
            }
        ],
        'pagination': {
            'next_key': None,
            'total': '1'
        }
    }
]

expected_proposals_1 = {
    'proposals': [
        {
            'proposal_id': '1',
            'title': 'Test Proposal Title',
            'description': 'Test Proposal Description',
            'status': 'passed',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        }
    ]
}

expected_proposals_2 = {
    'proposals': [
        {
            'proposal_id': '1',
            'title': 'Test Proposal Title',
            'description': 'Test Proposal Description',
            'status': 'rejected',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        },
        {
            'proposal_id': '2',
            'title': 'Test Proposal Title 2',
            'description': 'Test Proposal Description 2',
            'status': 'voting_period',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        }
    ]
}

expected_proposals_3 = {
    'proposals': [
        {
            'proposal_id': '1',
            'title': 'Test Proposal Title',
            'description': 'Test Proposal Description',
            'status': 'rejected',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        },
        {
            'proposal_id': '2',
            'title': 'Test Proposal Title 2',
            'description': 'Test Proposal Description 2',
            'status': 'voting_period',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        },
        {
            'proposal_id': '3',
            'title': 'Test Proposal Title 3',
            'description': 'Test Proposal Description 3',
            'status': 'deposit_period',
            'final_tally_result': {
                'yes': '100',
                'abstain': '100',
                'no': '100',
                'no_with_veto': '100'
            },
            'submit_time': '2019-03-20T06:41:27.040075748Z',
            'deposit_end_time': '2019-04-03T06:41:27.040075748Z',
            'total_deposit': [
                {
                    'denom': 'uatom',
                    'amount': '512100000'
                }
            ],
            'voting_start_time': '2019-03-20T20:43:59.630492307Z',
            'voting_end_time': '2019-04-03T20:43:59.630492307Z'
        }
    ]
}


class TestCosmosNetworkMonitor(unittest.TestCase):
    def setUp(self) -> None:
        # Dummy data
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.test_data_dict = {
            'test_key_1': 'test_val_1',
            'test_key_2': 'test_val_2',
        }
        self.test_queue_name = 'Test Queue'
        self.test_exception = PANICException('test_exception', 1)
        self.retrieved_proposals_example = expected_proposals_1

        # Rabbit connection
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        # Monitor instance
        self.cosmos_test_nodes = CosmosTestNodes()
        self.monitor_name = 'test_monitor'
        self.monitoring_period = 10
        self.parent_id = 'test_parent_id'
        self.chain_name = 'cosmoshub'
        self.data_sources = [
            self.cosmos_test_nodes.pruned_non_validator,
            self.cosmos_test_nodes.archive_non_validator,
            self.cosmos_test_nodes.archive_validator
        ]
        self.test_monitor = CosmosNetworkMonitor(
            self.monitor_name, self.data_sources, self.parent_id,
            self.chain_name, self.dummy_logger, self.monitoring_period,
            self.rabbitmq)

        self.received_retrieval_info = {
            'cosmos_rest': {
                'data': self.retrieved_proposals_example,
                'data_retrieval_failed': False,
                'data_retrieval_exception': None,
                'get_function': self.test_monitor._get_cosmos_rest_data,
                'processing_function':
                    self.test_monitor._process_retrieved_cosmos_rest_data,
                'monitoring_enabled': True
            }
        }

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_monitor.rabbitmq)
        delete_queue_if_exists(self.test_monitor.rabbitmq, self.test_queue_name)
        delete_exchange_if_exists(self.test_monitor.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_monitor.rabbitmq, RAW_DATA_EXCHANGE)
        disconnect_from_rabbit(self.test_monitor.rabbitmq)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_exception = None
        self.cosmos_test_nodes.clear_attributes()
        self.cosmos_test_nodes = None
        self.test_monitor = None

    def test_parent_id_returns_parent_id(self) -> None:
        self.assertEqual(self.parent_id, self.test_monitor.parent_id)

    def test_chain_name_returns_chain_name(self) -> None:
        self.assertEqual(self.chain_name, self.test_monitor.chain_name)

    @parameterized.expand([
        (retrieved_proposals_1_v1, expected_proposals_1),
        (retrieved_proposals_1_v2, expected_proposals_1),
        (retrieved_proposals_2_v1, expected_proposals_2),
        (retrieved_proposals_2_v2, expected_proposals_2)
    ])
    @mock.patch.object(CosmosRestServerApiWrapper,
                       'get_proposals_v0_39_2')
    def test_get_cosmos_rest_v0_39_2_indirect_data_proposals_return(
            self, proposals_return, expected_return,
            mock_proposals) -> None:
        """
        We will check that the return is as expected for all cases
        """
        mock_proposals.return_value = proposals_return
        actual_return = \
            self.test_monitor._get_cosmos_rest_v0_39_2_indirect_data(
                self.data_sources[0])
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        (retrieved_proposals_1_v3, expected_proposals_1),
        (retrieved_proposals_1_v4, expected_proposals_1),
        (retrieved_proposals_2_v3, expected_proposals_2),
        (retrieved_proposals_2_v4, expected_proposals_2)
    ])
    @mock.patch.object(CosmosRestServerApiWrapper,
                       'get_proposals_v0_42_6')
    def test_get_cosmos_rest_v0_42_6_indirect_data_proposals_return(
            self, proposals_return, expected_return,
            mock_proposals) -> None:
        """
        We will check that the return is as expected for all cases
        """
        mock_proposals.return_value = proposals_return
        actual_return = \
            self.test_monitor._get_cosmos_rest_v0_42_6_indirect_data(
                self.data_sources[0])
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        (retrieved_proposals_3_v1, expected_proposals_3),
        (retrieved_proposals_3_v2, expected_proposals_3),
    ])
    @mock.patch.object(CosmosRestServerApiWrapper, 'get_proposals_v0_42_6')
    def test_get_cosmos_rest_v0_42_6_indirect_data_proposals_pagination_return(
            self, proposals_returns, expected_return, mock_proposals) -> None:
        """
        We will check that the return is as expected for all cases
        """
        mock_proposals.side_effect = proposals_returns
        actual_return = \
            self.test_monitor._get_cosmos_rest_v0_42_6_indirect_data(
                self.data_sources[0])
        self.assertEqual(expected_return, actual_return)

    @freeze_time("2012-01-01")
    def test_process_error_returns_expected_data(self) -> None:
        expected_output = {
            'error': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'parent_id': self.test_monitor.parent_id,
                    'chain_name': self.test_monitor.chain_name,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }
        actual_output = self.test_monitor._process_error(self.test_exception)
        self.assertEqual(actual_output, expected_output)

    @freeze_time("2012-01-01")
    def test_process_retrieved_cosmos_rest_data_returns_expected_data(
            self) -> None:
        expected_output = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'parent_id': self.test_monitor.parent_id,
                    'chain_name': self.test_monitor.chain_name,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'data': self.retrieved_proposals_example
            }
        }

        actual_output = self.test_monitor._process_retrieved_cosmos_rest_data(
            self.retrieved_proposals_example)
        self.assertEqual(expected_output, actual_output)

    def test_send_data_sends_data_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_data, and checks that the data is
        # received
        self.test_monitor._initialise_rabbitmq()

        # Delete the queue before to avoid messages in the queue on error.
        self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
            routing_key=COSMOS_NETWORK_RAW_DATA_ROUTING_KEY)

        self.test_monitor._send_data(self.test_data_dict)

        # By re-declaring the queue again we can get the number of messages in
        # the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the processed data
        _, _, body = self.test_monitor.rabbitmq.basic_get(self.test_queue_name)
        self.assertEqual(self.test_data_dict, json.loads(body))

    @freeze_time("2012-01-01")
    @mock.patch.object(CosmosNetworkMonitor, "_send_data")
    @mock.patch.object(CosmosNetworkMonitor, "_send_heartbeat")
    @mock.patch.object(CosmosNetworkMonitor, "_get_data")
    def test_monitor_sends_data_and_hb_if_data_retrieve_and_processing_success(
            self, mock_get_data, mock_send_hb, mock_send_data) -> None:
        expected_output_data = {
            'cosmos_rest': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'parent_id': self.test_monitor.parent_id,
                        'chain_name': self.test_monitor.chain_name,
                        'time': datetime(2012, 1, 1).timestamp()
                    },
                    'data': self.retrieved_proposals_example,
                }
            }
        }
        expected_output_hb = {
            'component_name': self.test_monitor.monitor_name,
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp()
        }

        mock_get_data.return_value = self.received_retrieval_info
        mock_send_data.return_value = None
        mock_send_hb.return_value = None

        self.test_monitor._monitor()

        mock_send_hb.assert_called_once_with(expected_output_hb)
        mock_send_data.assert_called_once_with(expected_output_data)

    @mock.patch.object(CosmosNetworkMonitor, "_send_data")
    @mock.patch.object(CosmosNetworkMonitor, "_send_heartbeat")
    @mock.patch.object(CosmosNetworkMonitor, "_process_data")
    @mock.patch.object(CosmosNetworkMonitor, "_get_data")
    def test_monitor_sends_no_data_and_hb_if_data_ret_success_and_proc_fails(
            self, mock_get_data, mock_process_data, mock_send_hb,
            mock_send_data) -> None:
        mock_process_data.side_effect = self.test_exception
        mock_get_data.return_value = self.received_retrieval_info
        mock_send_data.return_value = None
        mock_send_hb.return_value = None

        self.test_monitor._monitor()
        mock_send_data.assert_not_called()
        mock_send_hb.assert_not_called()

    @mock.patch.object(CosmosNetworkMonitor, "_send_data")
    @mock.patch.object(CosmosNetworkMonitor, "_send_heartbeat")
    @mock.patch.object(CosmosNetworkMonitor, "_get_data")
    def test_monitor_sends_no_data_and_no_hb_on_get_data_unexpected_exception(
            self, mock_get_data, mock_send_hb, mock_send_data) -> None:
        mock_get_data.side_effect = self.test_exception
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        self.assertRaises(PANICException, self.test_monitor._monitor)
        mock_send_data.assert_not_called()
        mock_send_hb.assert_not_called()

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (MessageWasNotDeliveredException,
         MessageWasNotDeliveredException('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(CosmosNetworkMonitor, "_send_data")
    @mock.patch.object(CosmosNetworkMonitor, "_get_data")
    def test_monitor_raises_error_if_raised_by_send_data(
            self, exception_class, exception_instance, mock_get_data,
            mock_send_data) -> None:
        mock_get_data.return_value = self.received_retrieval_info
        mock_send_data.side_effect = exception_instance
        self.assertRaises(exception_class, self.test_monitor._monitor)

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (MessageWasNotDeliveredException,
         MessageWasNotDeliveredException('test'),),
        (Exception, Exception('test'),),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(CosmosNetworkMonitor, "_send_data")
    @mock.patch.object(CosmosNetworkMonitor, "_send_heartbeat")
    @mock.patch.object(CosmosNetworkMonitor, "_get_data")
    def test_monitor_raises_error_if_raised_by_send_hb(
            self, exception_class, exception_instance, mock_get_data,
            mock_send_hb, mock_send_data) -> None:
        mock_get_data.return_value = self.received_retrieval_info
        mock_send_data.return_value = None
        mock_send_hb.side_effect = exception_instance
        self.assertRaises(exception_class, self.test_monitor._monitor)
