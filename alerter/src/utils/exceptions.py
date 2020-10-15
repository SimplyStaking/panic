class PANICException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
        super().__init__(self.message, self.code)


class ConnectionNotInitializedException(PANICException):
    def __init__(self, component):
        message = "Did not initialize a connection with {}" \
            .format(component)
        code = 5000
        super().__init__(message, code)


class MessageWasNotDeliveredException(PANICException):
    def __init__(self, err):
        message = "Message could not be delivered. Error: {}".format(err)
        code = 5001
        super().__init__(message, code)


class NoMetricsGivenException(PANICException):

    def __init__(self, message: str) -> None:
        message = message
        code = 5002
        super().__init__(message, code)


class MetricNotFoundException(PANICException):

    def __init__(self, metric, endpoint) -> None:
        message = "Could not find metric {} at endpoint {}" \
            .format(metric, endpoint)
        code = 5003
        super().__init__(message, code)


class SystemIsDownException(PANICException):

    def __init__(self, system_name) -> None:
        message = "System {] is unreachable".format(system_name)
        code = 5004
        super().__init__(message, code)


class DataReadingException(PANICException):

    def __init__(self, system_monitor_name, system_name) -> None:
        message = "System monitor {} experienced errors when reading " \
                  "data from {}".format(system_monitor_name, system_name)
        code = 5005
        super().__init__(message, code)
