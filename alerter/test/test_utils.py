from time import sleep

import pika

from src.alerter.alert_code import AlertCode
from src.message_broker.rabbitmq import RabbitMQApi


def infinite_fn() -> None:
    while True:
        sleep(10)


class DummyAlertCode(AlertCode):
    TEST_ALERT_CODE = 'test_alert_code'


def connect_to_rabbit(rabbit: RabbitMQApi, attempts: int = 3) -> None:
    tries = 0

    while tries < attempts:
        try:
            rabbit.connect()
            return
        except Exception as e:
            tries += 1
            print("Could not connect to rabbit. Attempts so far: {}".format(
                tries))
            print(e)
            if tries >= attempts:
                raise e


def disconnect_from_rabbit(rabbit: RabbitMQApi, attempts: int = 3) -> None:
    tries = 0

    while tries < attempts:
        try:
            rabbit.disconnect()
            return
        except Exception as e:
            tries += 1
            print(
                "Could not disconnect to rabbit. Attempts so far: {}"
                    .format(tries)
            )
            print(e)
            if tries >= attempts:
                raise e


def delete_exchange_if_exists(rabbit: RabbitMQApi, exchange_name: str) -> None:
    try:
        rabbit.exchange_declare(exchange_name, passive=True)
        rabbit.exchange_delete(exchange_name)
    except pika.exceptions.ChannelClosedByBroker:
        print("Exchange {} does not exist - don't need to close".format(
            exchange_name))


def delete_queue_if_exists(rabbit: RabbitMQApi, queue_name: str) -> None:
    try:
        rabbit.queue_declare(queue_name, passive=True)
        rabbit.queue_purge(queue_name)
        rabbit.queue_delete(queue_name)
    except pika.exceptions.ChannelClosedByBroker:
        print("Queue {} does not exist - don't need to close".format(
            queue_name
        ))
