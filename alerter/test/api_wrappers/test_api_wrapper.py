import logging
import unittest
from typing import Any

from src.api_wrappers.api_wrapper import ApiWrapper


class DummyApiWrapper(ApiWrapper):
    """
    This class is going to be used to test the logic inside the ApiWrapper
    class. A dummy class must be used because the ApiWrapper class contains some
    abstract methods.
    """

    def __init__(self, logger: logging.Logger, verify: bool = False,
                 timeout: int = 10) -> None:
        super().__init__(logger, verify, timeout)

    def execute_with_checks(self, *args) -> Any:
        pass


class TestApiWrapper(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.verify = True
        self.timeout = 20

        # Test instance
        self.test_wrapper = DummyApiWrapper(self.dummy_logger, self.verify,
                                            self.timeout)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.test_wrapper = None

    def test_logger_returns_logger(self) -> None:
        self.assertEqual(self.dummy_logger, self.test_wrapper.logger)

    def test_verify_returns_verify(self) -> None:
        self.assertEqual(self.verify, self.test_wrapper.verify)

    def test_timeout_returns_timeout(self) -> None:
        self.assertEqual(self.timeout, self.test_wrapper.timeout)
