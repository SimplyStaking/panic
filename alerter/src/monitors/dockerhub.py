import copy
import json
import logging
from datetime import datetime
from http.client import IncompleteRead
from typing import Dict, List

import pika
import pika.exceptions
from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError)
from urllib3.exceptions import ProtocolError

from src.configs.repo import DockerHubRepoConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.monitor import Monitor
from src.utils.constants.rabbitmq import (RAW_DATA_EXCHANGE,
                                          DOCKERHUB_RAW_DATA_ROUTING_KEY)
from src.utils.data import get_json
from src.utils.datetime import json_to_unix_time
from src.utils.exceptions import (DataReadingException, PANICException,
                                  CannotAccessDockerHubPageException,
                                  DockerHubAPICallException,
                                  JSONDecodeException)


class DockerHubMonitor(Monitor):
    def __init__(self, monitor_name: str, repo_config: DockerHubRepoConfig,
                 logger: logging.Logger, monitor_period: int,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(monitor_name, logger, monitor_period, rabbitmq)
        self._repo_config = repo_config

    @property
    def repo_config(self) -> DockerHubRepoConfig:
        return self._repo_config

    def _display_data(self, data: Dict) -> str:
        # To cater for tags with unicode characters we must first encode
        # as utf-8 and then decode
        return json.dumps(data, ensure_ascii=False).encode('utf8').decode()

    def _get_data(self) -> List:
        pages = [get_json(self.repo_config.tags_page, self.logger)]
        i = 0
        while pages[i]['next']:
            pages.append(get_json(pages[i]['next'], self.logger))
            i += 1
        return pages

    def _process_error(self, error: PANICException) -> Dict:
        processed_data = {
            'error': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'repo_namespace': self.repo_config.repo_namespace,
                    'repo_name': self.repo_config.repo_name,
                    'repo_id': self.repo_config.repo_id,
                    'repo_parent_id': self.repo_config.parent_id,
                    'time': datetime.now().timestamp()
                },
                'message': error.message,
                'code': error.code,
            }
        }

        return processed_data

    def _process_retrieved_data(self, data: Dict) -> Dict:
        data_copy = copy.deepcopy(data)

        # Add some meta-data to the processed data
        processed_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'repo_namespace': self.repo_config.repo_namespace,
                    'repo_name': self.repo_config.repo_name,
                    'repo_id': self.repo_config.repo_id,
                    'repo_parent_id': self.repo_config.parent_id,
                    'time': datetime.now().timestamp()
                },
                'data': {},
            }
        }

        tag_names, tag_timestamps = [], []
        for i in range(len(data_copy)):
            for j in range(len(data_copy[i]['results'])):
                tag_names.append(data_copy[i]['results'][j]['name'])
                tag_timestamps.append(
                    data_copy[i]['results'][j]['last_updated'])

        for i in range(len(tag_names)):
            processed_data['result']['data'][str(i)] = {}
            processed_data['result']['data'][str(i)]['tag_name'] = tag_names[i]
            processed_data['result']['data'][str(i)]['last_updated'] = \
                json_to_unix_time(tag_timestamps[i])

            self.logger.debug("%s tags_info: %s", self.repo_config,
                              json.dumps(
                                  processed_data['result']['data'][str(i)],
                                  ensure_ascii=False).encode('utf8').decode())

        return processed_data

    def _send_data(self, data: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE,
            routing_key=DOCKERHUB_RAW_DATA_ROUTING_KEY, body=data,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent data to '%s' exchange.", RAW_DATA_EXCHANGE)

    def _monitor(self) -> None:
        data_retrieval_exception = None
        data = None
        data_retrieval_failed = True
        try:
            data = self._get_data()

            # If response has zero count, then the repo doesn't exist
            if data[0]['count'] == 0:
                data_retrieval_exception = DockerHubAPICallException()
                self.logger.error("Error when retrieving data from %s: "
                                  "(%s, %s)", self.repo_config.__str__(),
                                  data_retrieval_exception.message,
                                  data_retrieval_exception.code)
            else:
                data_retrieval_failed = False
        except (ReqConnectionError, ReadTimeout):
            data_retrieval_exception = CannotAccessDockerHubPageException(
                self.repo_config.tags_page)
            self.logger.error("Error when retrieving data from %s",
                              self.repo_config.tags_page)
            self.logger.exception(data_retrieval_exception)
        except (IncompleteRead, ChunkedEncodingError, ProtocolError):
            data_retrieval_exception = DataReadingException(
                self.monitor_name, self.repo_config.tags_page)
            self.logger.error("Error when retrieving data from %s",
                              self.repo_config.tags_page)
            self.logger.exception(data_retrieval_exception)
        except json.JSONDecodeError as e:
            data_retrieval_exception = JSONDecodeException(e)
            self.logger.error("Error when retrieving data from %s",
                              self.repo_config.tags_page)
            self.logger.exception(data_retrieval_exception)

        try:
            processed_data = self._process_data(data_retrieval_failed,
                                                [data_retrieval_exception],
                                                [data])
        except Exception as error:
            self.logger.error("Error when processing data obtained from %s",
                              self.repo_config.tags_page)
            self.logger.exception(error)
            # Do not send data if we experienced processing errors
            return

        self._send_data(processed_data)

        if not data_retrieval_failed:
            # Only output the gathered metrics if there was no error
            self.logger.debug(self._display_data(
                processed_data['result']['data']))

        # Send a heartbeat only if the entire round was successful
        heartbeat = {
            'component_name': self.monitor_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        self._send_heartbeat(heartbeat)
