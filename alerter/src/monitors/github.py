import json
import logging
from datetime import datetime
from http.client import IncompleteRead
from typing import Dict

import pika
import pika.exceptions
from requests.exceptions import ConnectionError as ReqConnectionError, \
    ReadTimeout, ChunkedEncodingError
from urllib3.exceptions import ProtocolError

from src.configs.repo import RepoConfig
from src.monitors.monitor import Monitor
from src.utils.constants import RAW_DATA_EXCHANGE
from src.utils.data import get_json
from src.utils.exceptions import DataReadingException, PANICException, \
    CannotAccessGitHubPageException, GitHubAPICallException


class GitHubMonitor(Monitor):
    def __init__(self, monitor_name: str, repo_config: RepoConfig,
                 logger: logging.Logger, monitor_period: int) -> None:
        super().__init__(monitor_name, logger, monitor_period)
        self._repo_config = repo_config
        self._releases_info = {}

    @property
    def repo_config(self) -> RepoConfig:
        return self._repo_config

    @property
    def releases_info(self) -> Dict:
        return self._releases_info

    def status(self) -> str:
        # To ensure no releases have unicode characters we must first encode
        # as utf-8 and then decode
        return json.dumps(self.releases_info, ensure_ascii=False) \
            .encode('utf8').decode()

    def _get_data(self) -> None:
        self._data = get_json(self.repo_config.releases_page, self.logger)

    def _process_data_retrieval_failed(self, error: PANICException) -> None:
        processed_data = {
            'error': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'repo_name': self.repo_config.repo_name,
                    'repo_id': self.repo_config.repo_id,
                    'repo_parent_id': self.repo_config.parent_id,
                    'time': str(datetime.now().timestamp())
                },
                'message': error.message,
                'code': error.code,
            }
        }

        self._data = processed_data

    def _process_data_retrieval_successful(self) -> None:
        # Add some meta-data to the processed data
        processed_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'repo_name': self.repo_config.repo_name,
                    'repo_id': self.repo_config.repo_id,
                    'repo_parent_id': self.repo_config.parent_id,
                    'time': str(datetime.now().timestamp())
                },
                'data': {},
            }
        }

        for i in range(len(self.data)):
            release_data = self.data[i]
            processed_data['result']['data'][i] = {}
            processed_data['result']['data'][i]['release_name'] = \
                release_data['name']
            processed_data['result']['data'][i]['tag_name'] = \
                release_data['tag_name']
            self.logger.debug("%s releases_info: %s",
                              self.repo_config,
                              json.dumps(
                                  processed_data['result']['data'][i]))
            self._releases_info[i] = processed_data['result']['data'][i]

        self._data = processed_data

    def _send_data(self) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE, routing_key='github', body=self.data,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent data to \'{}\' exchange.".format(
            RAW_DATA_EXCHANGE))

    def _monitor(self) -> None:
        data_retrieval_exception = Exception()
        try:
            self._get_data()

            # If response contains a message this indicate an error in the
            # GitHub API Call
            if 'message' in self.data:
                self._data_retrieval_failed = True
                data_retrieval_exception = GitHubAPICallException(
                    self.data['message'])
                self.logger.error("Error when retrieving data from {}: ({}, {})"
                                  .format(self.repo_config.releases_page,
                                          data_retrieval_exception.message,
                                          data_retrieval_exception.code))
            else:
                self._data_retrieval_failed = False
        except (ReqConnectionError, ReadTimeout):
            self._data_retrieval_failed = True
            data_retrieval_exception = CannotAccessGitHubPageException(
                self.repo_config.releases_page)
            self.logger.error("Error when retrieving data from {}"
                              .format(self.repo_config.releases_page))
            self.logger.exception(data_retrieval_exception)
        except (IncompleteRead, ChunkedEncodingError, ProtocolError):
            self._data_retrieval_failed = True
            data_retrieval_exception = DataReadingException(
                self.monitor_name, self.repo_config.releases_page)
            self.logger.error("Error when retrieving data from {}"
                              .format(self.repo_config.releases_page))
            self.logger.exception(data_retrieval_exception)
        except json.JSONDecodeError as e:
            self._data_retrieval_failed = True
            data_retrieval_exception = e
            self.logger.error("Error when retrieving data from {}"
                              .format(self.repo_config.releases_page))
            self.logger.exception(data_retrieval_exception)

        try:
            self._process_data(data_retrieval_exception)
        except Exception as error:
            self.logger.error("Error when processing data obtained from {}"
                              .format(self.repo_config.releases_page))
            self.logger.exception(error)
            # Do not send data if we experienced processing errors
            return

        self._send_data()

        # Only output the gathered data if there was no error
        if not self.data_retrieval_failed:
            self.logger.info(self.status())
