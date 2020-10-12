class ConnectionNotInitializedException(Exception):
    def __init__(self, component):
        self.message = "Did not initialize a connection with {}" \
            .format(component)
        self.code = 5000
        super().__init__(self.message, self.code)


class MessageWasNotDeliveredException(Exception):
    def __init__(self, err):
        self.message = "Message could not be delivered. Error: {}".format(err)
        self.code = 5001
        super().__init__(self.message, self.code)


class NoMetricsGivenException(Exception):

    def __init__(self, message: str) -> None:
        self.message = message
        self.code = 5002
        super().__init__(self.message, self.code)


class MetricNotFoundException(Exception):

    def __init__(self, metric, endpoint) -> None:
        self.message = "Could not find metric {} at endpoint {}"\
            .format(metric, endpoint)
        self.code = 5003
        super().__init__(self.message, self.code)