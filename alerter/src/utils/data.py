import logging

import requests


def get_prometheus(endpoint: str, logger: logging.Logger):
    try:
        metrics = requests.get(endpoint).content
        logger.debug('Retrieved prometheus data from endpoint: ' + endpoint)
        return metrics.decode("utf-8")
    except requests.exceptions.RequestException as e:
        raise RequestCallFailedException('Failed to retrieve data from: ' + \
                                         endpoint)

# TODO: Need to see what possible errors can be raised
# TODO: Possibly catch alerts from the outside only