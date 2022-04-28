import unittest
from unittest.mock import Mock

from parameterized import parameterized

from src.utils.data import transformed_data_processing_helper
from src.utils.exceptions import ReceivedUnexpectedDataException
from test.test_utils.utils import dummy_function, dummy_none_function


class TestDataUtils(unittest.TestCase):

    @parameterized.expand([
        ({'prometheus': {'error': 4}, 'rpc': {'bad_index_key': {}, }, },),
        ({'prometheus': {}, 'rpc': {}, },),
        ({'prometheus': {}, },),
        ({},),
    ])
    def test_trans_data_proc_helper_raises_ReceivedUnexpectDataExcept_bad_data(
            self, test_trans_data) -> None:
        # Note that for this test we will only consider the data's structure,
        # not the metrics.
        test_config = {
            'prometheus': {
                'result': dummy_function,
                'error': dummy_none_function,
            },
            'rpc': {
                'result': dummy_function,
                'error': dummy_none_function,
            },
        }

        self.assertRaises(ReceivedUnexpectedDataException,
                          transformed_data_processing_helper, 'test_component',
                          test_config, test_trans_data)

    def test_process_store_calls_correct_function_for_sources(self) -> None:
        test_result_fn = Mock(return_value="result")
        test_error_fn = Mock(return_value="error")
        test_config = {
            'prometheus': {
                'result': test_result_fn,
                'error': test_error_fn,
            },
            'rpc': {
                'result': test_result_fn,
                'error': test_error_fn,
            }
        }
        test_trans_data = {
            'prometheus': {
                'error': 20,
            },
            'rpc': {
                'result': 10
            }
        }

        transformed_data_processing_helper('test_component', test_config,
                                           test_trans_data)

        test_result_fn.assert_called_once_with(10)
        test_error_fn.assert_called_once_with(20)
