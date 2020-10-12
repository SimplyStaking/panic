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
