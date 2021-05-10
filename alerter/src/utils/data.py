import json
import logging
from enum import Enum
from typing import Dict

import requests
from prometheus_client.parser import text_string_to_metric_families

from src.utils.exceptions import (NoMetricsGivenException,
                                  MetricNotFoundException)


class RequestStatus(Enum):
    SUCCESS = True
    FAILED = False


def get_json(endpoint: str, logger: logging.Logger, params=None,
             verify: bool = True):
    if params is None:
        params = {}
    get_ret = requests.get(url=endpoint, params=params, timeout=15,
                           verify=verify)
    logger.debug("get_json: get_ret: %s", get_ret)
    return json.loads(get_ret.content.decode('UTF-8'))


def get_prometheus(endpoint: str, logger: logging.Logger, verify: bool = True):
    metrics = requests.get(endpoint, timeout=10, verify=verify).content
    logger.debug("Retrieved prometheus data from endpoint: " + endpoint)
    return metrics.decode('utf-8')


def get_prometheus_metrics_data(endpoint: str,
                                requested_metrics: Dict[str, str],
                                logger: logging.Logger,
                                verify: bool = True) -> Dict:
    """
    :param endpoint: The endpoint we are obtaining the data from
    :param requested_metrics: A dict which is expected with the following
    structure:
    {
        "metric": "optional" | any string
    }
    Where if the metric is set as "optional" an exception is not raised if that
    metric is not found. Furthermore, this function will set the metric's value
    to None if this is the case.
    If the metric is not set as optional and it cannot be found at the data
    source its value is set as None.
    :param logger: Where logging should be sent
    :param verify: Will verify the certificate if set to True
    :return: The metrics with their values
    """
    response = {}
    if len(requested_metrics) == 0:
        raise NoMetricsGivenException("No metrics given when requesting "
                                      "prometheus data from " + endpoint)

    metrics = get_prometheus(endpoint, logger, verify)
    for family in text_string_to_metric_families(metrics):
        for sample in family.samples:
            if sample.name in requested_metrics:
                if sample.name not in response:
                    if sample.labels != {}:
                        response[sample.name] = {}
                        response[sample.name][json.dumps(sample.labels)] = \
                            sample.value
                    else:
                        response[sample.name] = sample.value
                else:
                    if sample.labels != {}:
                        response[sample.name][json.dumps(sample.labels)] = \
                            sample.value
                    else:
                        response[sample.name] = sample.value + \
                                                response[sample.name]

    missing_metrics = set(requested_metrics) - set(response)
    for metric in missing_metrics:
        if requested_metrics[metric].lower() == "optional":
            response[metric] = None
        else:
            raise MetricNotFoundException(metric, endpoint)

    return response
