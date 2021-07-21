import unittest
from typing import Dict

from src.configs.factory.configs_factory import ConfigsFactory


class ConfigsFactoryInstance(ConfigsFactory):
    def __init__(self, configs: Dict) -> None:
        super().__init__()
        self._configs = configs

    def remove_config(self, *args) -> None:
        pass

    def add_new_config(self, *args) -> None:
        pass


class TestConfigsFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.test_configs = {
            'test_key': 'test_val'
        }
        self.test_factory_instance = ConfigsFactoryInstance(self.test_configs)

    def tearDown(self) -> None:
        self.test_configs = None
        self.test_factory_instance = None

    def test_configs_returns_saved_configs(self) -> None:
        self.assertEqual(self.test_configs,
                         self.test_factory_instance.configs)
