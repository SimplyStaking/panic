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

from alerter.src.configs.repo import RepoConfig
from alerter.src.monitors.monitor import Monitor
from alerter.src.utils.data import get_json
from alerter.src.utils.exceptions import DataReadingException, PANICException, \
    CannotAccessGitHubPageException, \
    GitHubAPICallException


class GitHubMonitor(Monitor):
    def __init__(self, monitor_name: str, repo_config: RepoConfig,
                 logger: logging.Logger, monitor_period: int) -> None:
        super().__init__(monitor_name, logger, monitor_period)
        self._repo_config = repo_config
        self._releases_info = None

    @property
    def repo_config(self) -> RepoConfig:
        return self._repo_config

    @property
    def releases_info(self) -> Dict:
        return self._releases_info

    def status(self) -> str:
        return json.dumps(self.releases_info)

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

        for release in self.data:
            release_data = self.data[release]
            processed_data['data'][release] = {}
            processed_data['data'][release]['release_name'] = \
                release_data['name']
            processed_data['data'][release]['tag_name'] = \
                release_data['tag_name']
            self.logger.debug('%s releases_info: %s',
                              self.repo_config,
                              json.dumps(processed_data['data'][release]))
            self._releases_info[release] = release_data

        self._data = processed_data

    def _send_data(self) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange='raw_data', routing_key='repo', body=self.data,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug('Sent data to \'raw_data\' exchange')

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
                self.logger.error('Error when retrieving data from {}'
                                  .format(self.repo_config.releases_page))
                self.logger.exception(data_retrieval_exception)
            else:
                self._data_retrieval_failed = False
        except (ReqConnectionError, ReadTimeout):
            self._data_retrieval_failed = True
            data_retrieval_exception = CannotAccessGitHubPageException(
                self.repo_config.releases_page)
            self.logger.error('Error when retrieving data from {}'
                              .format(self.repo_config.releases_page))
            self.logger.exception(data_retrieval_exception)
        except (IncompleteRead, ChunkedEncodingError, ProtocolError):
            self._data_retrieval_failed = True
            data_retrieval_exception = DataReadingException(
                self.monitor_name, self.repo_config.releases_page)
            self.logger.error('Error when retrieving data from {}'
                              .format(self.repo_config.releases_page))
            self.logger.exception(data_retrieval_exception)
        except json.JSONDecodeError as e:
            self._data_retrieval_failed = True
            data_retrieval_exception = e
            self.logger.error('Error when retrieving data from {}'
                              .format(self.repo_config.releases_page))
            self.logger.exception(data_retrieval_exception)
        self._process_data(data_retrieval_exception)
        self._send_data()
