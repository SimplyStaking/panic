import copy
import json
import logging
from datetime import datetime
from typing import List

import pika.exceptions

from src.alerter.alert_severities import Severity
from src.alerter.alerters.alerter import Alerter
from src.alerter.alerts.dockerhub_alerts import (
    CannotAccessDockerHubPageAlert,
    DockerHubNewTagAlert,
    DockerHubUpdatedTagAlert,
    DockerHubDeletedTagAlert,
    DockerHubPageNowAccessibleAlert, DockerHubTagsAPICallErrorAlert,
    DockerHubTagsAPICallErrorResolvedAlert)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    DOCKERHUB_ALERTER_INPUT_QUEUE_NAME,
    DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY,
    DOCKERHUB_ALERT_ROUTING_KEY, TOPIC)
from src.utils.dictionaries import (dict_2d_value_diff_by_key,
                                    dict_2d_value_intersection_by_key)
from src.utils.exceptions import (MessageWasNotDeliveredException,
                                  ReceivedUnexpectedDataException,
                                  CannotAccessDockerHubPageException,
                                  DockerHubAPICallException)


class DockerhubAlerter(Alerter):
    def __init__(self, alerter_name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi, max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)
        self._cannot_access_dockerhub_page = {}
        self._tags_api_call_error = {}

    def _initialise_rabbitmq(self) -> None:
        # An alerter is both a consumer and producer, therefore we need to
        # initialise both the consuming and producing configurations.
        self.rabbitmq.connect_till_successful()

        # Set consuming configuration
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)
        self.rabbitmq.exchange_declare(exchange=ALERT_EXCHANGE,
                                       exchange_type=TOPIC, passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.logger.info("Creating queue '%s'",
                         DOCKERHUB_ALERTER_INPUT_QUEUE_NAME)
        self.rabbitmq.queue_declare(DOCKERHUB_ALERTER_INPUT_QUEUE_NAME,
                                    passive=False, durable=True,
                                    exclusive=False, auto_delete=False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", DOCKERHUB_ALERTER_INPUT_QUEUE_NAME,
                         ALERT_EXCHANGE, DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            queue=DOCKERHUB_ALERTER_INPUT_QUEUE_NAME, exchange=ALERT_EXCHANGE,
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(queue=DOCKERHUB_ALERTER_INPUT_QUEUE_NAME,
                                    on_message_callback=self._process_data,
                                    auto_ack=False, exclusive=False,
                                    consumer_tag=None)

        # Pre-fetch count is 10 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)

        # Set producing configuration
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _create_state_for_dockerhub(self, dockerhub_id: str) -> None:
        if dockerhub_id not in self._cannot_access_dockerhub_page:
            self._cannot_access_dockerhub_page[dockerhub_id] = False
        if dockerhub_id not in self._tags_api_call_error:
            self._tags_api_call_error[dockerhub_id] = False

    def _process_data(self,
                      ch: pika.adapters.blocking_connection.BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:
        data_received = json.loads(body)
        self.logger.debug("Received %s. Now processing this data.",
                          data_received)

        processing_error = False
        data_for_alerting = []
        try:
            if 'result' in data_received:
                meta = data_received['result']['meta_data']
                data = data_received['result']['data']

                self._create_state_for_dockerhub(meta['repo_id'])

                if self._cannot_access_dockerhub_page[meta['repo_id']]:
                    alert = DockerHubPageNowAccessibleAlert(
                        meta['repo_namespace'],
                        meta['repo_name'], Severity.INFO.value,
                        meta['last_monitored'], meta['repo_parent_id'],
                        meta['repo_id'])
                    data_for_alerting.append((None, alert.alert_data))
                    self.logger.debug("Successfully classified alert %s",
                                      alert.alert_data)
                    self._cannot_access_dockerhub_page[meta['repo_id']] = False

                if self._tags_api_call_error[meta['repo_id']]:
                    alert = DockerHubTagsAPICallErrorResolvedAlert(
                        meta['repo_namespace'],
                        meta['repo_name'], Severity.INFO.value,
                        meta['last_monitored'], meta['repo_parent_id'],
                        meta['repo_id'])
                    data_for_alerting.append((None, alert.alert_data))
                    self.logger.debug("Successfully classified alert %s",
                                      alert.alert_data)
                    self._tags_api_call_error[
                        meta['repo_id']] = False

                current = data['current']
                previous = data['previous']
                if previous is not None:

                    # See which tags have been deleted, and which are new
                    deleted = dict_2d_value_diff_by_key(
                        previous, current, 'tag_name')
                    new = dict_2d_value_diff_by_key(
                        current, previous, 'tag_name')

                    # See if the ones which remained have been updated
                    updated = []
                    for key, pair in dict_2d_value_intersection_by_key(
                            current, previous, 'tag_name').items():
                        if pair[0]['last_updated'] != pair[1]['last_updated']:
                            updated.append({
                                'tag_name': key,
                                'last_updated': pair[0]['last_updated']
                            })

                    # Create alerts for each type
                    for tag in deleted:
                        alert = DockerHubDeletedTagAlert(
                            meta['repo_namespace'],
                            meta['repo_name'],
                            tag['tag_name'],
                            Severity.INFO.value,
                            meta['last_monitored'], meta['repo_parent_id'],
                            meta['repo_id']
                        )
                        data_for_alerting.append(
                            (tag['last_updated'], alert.alert_data))
                        self.logger.debug("Successfully classified alert %s",
                                          alert.alert_data)

                    for tag in new:
                        alert = DockerHubNewTagAlert(
                            meta['repo_namespace'],
                            meta['repo_name'],
                            tag['tag_name'],
                            Severity.INFO.value,
                            meta['last_monitored'], meta['repo_parent_id'],
                            meta['repo_id']
                        )
                        data_for_alerting.append(
                            (tag['last_updated'], alert.alert_data))
                        self.logger.debug("Successfully classified alert %s",
                                          alert.alert_data)

                    for tag in updated:
                        alert = DockerHubUpdatedTagAlert(
                            meta['repo_namespace'],
                            meta['repo_name'],
                            tag['tag_name'],
                            Severity.INFO.value,
                            meta['last_monitored'], meta['repo_parent_id'],
                            meta['repo_id']
                        )
                        data_for_alerting.append(
                            (tag['last_updated'], alert.alert_data))
                        self.logger.debug("Successfully classified alert %s",
                                          alert.alert_data)

            elif 'error' in data_received:
                """
                CannotAccessDockerhubPageAlert and 
                DockerHubTagsAPICallErrorAlert repeats constantly on each
                monitoring round (DEFAULT: 1 hour). This has repeat timer as
                it's an indication that the configuration is wrong and should
                be fixed.
                """
                error_code = int(data_received['error']['code'])
                error_message = data_received['error']['message']
                meta_data = data_received['error']['meta_data']

                self._create_state_for_dockerhub(meta_data['repo_id'])

                if error_code == CannotAccessDockerHubPageException.code:
                    alert = CannotAccessDockerHubPageAlert(
                        meta_data['repo_namespace'], meta_data['repo_name'],
                        Severity.ERROR.value, meta_data['time'],
                        meta_data['repo_parent_id'], meta_data['repo_id']
                    )
                    data_for_alerting.append((None, alert.alert_data))
                    self.logger.debug("Successfully classified alert %s",
                                      alert.alert_data)
                    self._cannot_access_dockerhub_page[
                        meta_data['repo_id']] = True
                elif self._cannot_access_dockerhub_page[meta_data['repo_id']]:
                    alert = DockerHubPageNowAccessibleAlert(
                        meta_data['repo_namespace'], meta_data['repo_name'],
                        Severity.INFO.value, meta_data['time'],
                        meta_data['repo_parent_id'], meta_data['repo_id']
                    )
                    data_for_alerting.append((None, alert.alert_data))
                    self.logger.debug("Successfully classified alert %s",
                                      alert.alert_data)
                    self._cannot_access_dockerhub_page[
                        meta_data['repo_id']] = False

                if error_code == DockerHubAPICallException.code:
                    alert = DockerHubTagsAPICallErrorAlert(
                        meta_data['repo_namespace'], meta_data['repo_name'],
                        Severity.ERROR.value, meta_data['time'],
                        meta_data['repo_parent_id'], meta_data['repo_id'],
                        error_message
                    )
                    data_for_alerting.append((None, alert.alert_data))
                    self.logger.debug("Successfully classified alert %s",
                                      alert.alert_data)
                    self._tags_api_call_error[
                        meta_data['repo_id']] = True
                elif self._tags_api_call_error[meta_data['repo_id']]:
                    alert = DockerHubTagsAPICallErrorResolvedAlert(
                        meta_data['repo_namespace'], meta_data['repo_name'],
                        Severity.INFO.value, meta_data['time'],
                        meta_data['repo_parent_id'], meta_data['repo_id']
                    )
                    data_for_alerting.append((None, alert.alert_data))
                    self.logger.debug("Successfully classified alert %s",
                                      alert.alert_data)
                    self._tags_api_call_error[
                        meta_data['repo_id']] = False
            else:
                raise ReceivedUnexpectedDataException("{}: _process_data"
                                                      "".format(self))
        except Exception as e:
            self.logger.error("Error when processing %s", data_received)
            self.logger.exception(e)
            processing_error = True

        # Place the data on the publishing queue if there is something to send.
        if len(data_for_alerting) != 0:
            # Sort the data
            data_for_alerting.sort(key=lambda x: (x[0] is not None, x[0]),
                                   reverse=False)
            data_for_alerting = [x[1] for x in data_for_alerting]

            self._place_latest_data_on_queue(data_for_alerting)

        # If the data is processed, it can be acknowledged.
        self.rabbitmq.basic_ack(method.delivery_tag, False)

        # Send any data waiting in the publisher queue, if any
        try:
            self._send_data()

            if not processing_error:
                heartbeat = {
                    'component_name': self.alerter_name,
                    'is_alive': True,
                    'timestamp': datetime.now().timestamp()
                }
                self._send_heartbeat(heartbeat)
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise it as message is residing in the
            # publisher queue.
            self.logger.exception(e)
        except Exception as e:
            # For any other exception raise it
            raise e

    def _place_latest_data_on_queue(self, data_list: List) -> None:
        # Place the latest alert data on the publishing queue. If the
        # queue is full, remove old data.
        for alert in data_list:
            self.logger.debug("Adding %s to the publishing queue.", alert)
            if self.publishing_queue.full():
                self.publishing_queue.get()
            self.publishing_queue.put({
                'exchange': ALERT_EXCHANGE,
                'routing_key': DOCKERHUB_ALERT_ROUTING_KEY,
                'data': copy.deepcopy(alert),
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True})
            self.logger.debug("%s added to the publishing queue successfully.",
                              alert)
