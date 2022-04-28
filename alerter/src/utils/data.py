import json
import logging
from enum import Enum
from json import JSONDecodeError
from typing import Dict

import requests
from prometheus_client.parser import text_string_to_metric_families

from src.utils.exceptions import (NoMetricsGivenException,
                                  MetricNotFoundException,
                                  ReceivedUnexpectedDataException)


class RequestStatus(Enum):
    SUCCESS = True
    FAILED = False


def get_cosmos_json(endpoint: str, logger: logging.Logger, params=None,
                    verify: bool = True, timeout=10):
    # For Cosmos SDK versions <= 0.39.2 a 404 not found error may be returned if
    # a function is deprecated. Hence we want to return the error and not
    # convert into JSON as this may raise a JSONDecodeError.
    if params is None:
        params = {}

    get_ret = requests.get(url=endpoint, params=params, timeout=timeout,
                           verify=verify, headers={'Connection': 'close'})
    logger.debug("get_json: get_ret: %s", get_ret)

    try:
        return json.loads(get_ret.content.decode('UTF-8'))
    except JSONDecodeError:
        return get_ret


def get_json(endpoint: str, logger: logging.Logger, params=None,
             verify: bool = True, timeout=10):
    if params is None:
        params = {}
    get_ret = requests.get(url=endpoint, params=params, timeout=timeout,
                           verify=verify, headers={'Connection': 'close'})
    logger.debug("get_json: get_ret: %s", get_ret)
    return json.loads(get_ret.content.decode('UTF-8'))


def get_prometheus(endpoint: str, logger: logging.Logger, verify: bool = True):
    metrics = requests.get(endpoint, timeout=10, verify=verify, headers={
        'Connection': 'close'}).content
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


def transformed_data_processing_helper(component_name: str, configuration: Dict,
                                       transformed_data: Dict,
                                       *other_args) -> None:
    """
    This function attempts to execute the appropriate processing function
    on the transformed data based on a configuration. If the transformed
    data is malformed, this function will raise an UnexpectedDataException
    :param configuration: A dict with the following schema:
                        {
                            '<source_name>': {
                                '<data_index_Key>': <related_processing_fn>
                            }
                        }
    :param transformed_data: The data received from the transformed
    :param component_name: The name fo the component receiving the transformed
                         : data
    :return: None
           : Raises an UnexpectedDataException if the transformed_data is
             malformed
    """
    processing_performed = False
    for source, processing_details in configuration.items():

        # If the required source is not in the transformed data, then the
        # transformed data is malformed, therefore raise an exception.
        if source not in transformed_data:
            raise ReceivedUnexpectedDataException(component_name)

        # If the source is enabled, process its transformed data.
        if transformed_data[source]:

            # Check which index_key was passed by the transformer and
            # execute the appropriate function.
            sub_processing_performed = False
            for data_index_key, processing_fn in processing_details.items():
                if data_index_key in transformed_data[source]:
                    processing_fn(transformed_data[source][data_index_key],
                                  *other_args)
                    processing_performed = True
                    sub_processing_performed = True
                    break

            # If this is false, it means that no processing fn could be
            # applied to the source's data
            if not sub_processing_performed:
                raise ReceivedUnexpectedDataException(component_name)

    # If no processing is performed, it means that the data was not
    # properly formatted, therefore raise an error.
    if not processing_performed:
        raise ReceivedUnexpectedDataException(component_name)
