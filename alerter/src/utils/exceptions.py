class ConnectionNotInitializedException(Exception):
    def __init__(self, component):
        self.message = "Did not initialize a connection with {}"\
            .format(component)
        super().__init__(self.message)


class MessageWasNotDeliveredException(Exception):
    def __init__(self, err):
        self.message = "Message could not be delivered. Error: {}".format(err)
        super().__init__(self.message)
