##################################
# This only serves as an example #
##################################

import logging

# For it to work with __name__ it must be in the alerter folder and not in the
# main script.
import os
import time

LOGGER = logging.getLogger("alerter")

if __name__ == '__main__':
    import sys
    from os import environ

    from alerter.src.config_manager import ConfigManager
    from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi

    # If this will be configurable we'll need this in the .env probably
    LOGGER.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler("./logs/example.log")

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%d/%m/%Y %I:%M:%S %p')

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    LOGGER.addHandler(console_handler)
    LOGGER.addHandler(file_handler)

    rabbit_ip = environ['RABBIT_IP']
    rabbit_port = environ['RABBIT_PORT']
    LOGGER.debug("Starting pub connection on IP %s with port %s", rabbit_ip,
                 rabbit_port)
    rabbit_pub = RabbitMQApi(host=rabbit_ip, port=rabbit_port)

    LOGGER.info("Starting config manager")
    LOGGER.info("Starting at %s", os.getcwd())
    cm = ConfigManager("./config", rabbit_pub)
    cm.start_watching_config_files()
    LOGGER.info("Logs reading from %s: %s", cm.config_directory,
                os.path.abspath(cm.config_directory))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        del cm  # __del__ stops watching the files
