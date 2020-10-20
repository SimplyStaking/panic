import logging

# For it to work with __name__ it must be in the alerter folder and not in the main script.
import os
import time

LOGGER = logging.getLogger("alerter")

if __name__ == '__main__':
    import sys
    from os import environ

    from alerter.src.config_manager import ConfigManager
    from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi

    LOGGER.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler("./logs/test2.log")

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%d/%m/%Y %I:%M:%S %p')

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    LOGGER.addHandler(console_handler)
    LOGGER.addHandler(file_handler)

    rabbit_ip = environ['RABBIT_IP']
    rabbit_port = environ['RABBIT_PORT']
    LOGGER.debug("Starting pub connection on IP %s with port %s", rabbit_ip, rabbit_port)
    rabbit_pub = RabbitMQApi(host=rabbit_ip, port=rabbit_port)

    LOGGER.info("Starting config manager")
    LOGGER.info("Starting at %s", os.getcwd())
    cm = ConfigManager("./config", rabbit_pub)
    cm.start_watching_config_files()
    LOGGER.info("Logs reading from %s: %s", cm.config_directory, os.path.abspath(cm.config_directory))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cm.stop_watching_config_files()
    # LOGGER.info("Starting consumer connection")
    # rabbit = RabbitMQApi(host=rabbit_ip, port=rabbit_port)
    # rabbit.connect_till_successful()
    #
    # rabbit.exchange_declare("config", "topic", False, True, False, False)
    #
    # result = rabbit.queue_declare(queue="", exclusive=True)
    # rabbit.queue_bind(exchange="config", queue=result.method.queue, routing_key="#")
    # LOGGER.info("Waiting for messages. To exit press CTRL+C")
    #
    #
    # def on_rabbit_recv(channel, method_frame, header_frame, body):
    #     logger = LOGGER.getChild("receiver")
    #     logger.info("Received message with Channel=%s, method_frame=%s, header_frame=%s, body=%r", channel,
    #                 method_frame, header_frame, body.decode())
    #
    # rabbit.basic_consume(queue=result.method.queue, on_message_callback=on_rabbit_recv)
    #
    # try:
    #     rabbit.start_consuming()
    # finally:
    #     LOGGER.info("Received CTRL+C. Disconnecting")
    #     print("Disconnecting")
    #     cm.stop_watching_config_files()
    #     rabbit.disconnect()
    #
    # LOGGER.critical("I am in a wrong place")
