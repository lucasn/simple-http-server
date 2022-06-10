class ServerException(Exception):
    def __init__(self, status, statusMessage, message=None, headers=[]):
        self.status = status
        self.statusMessage = statusMessage
        self.message = message
        self.headers = headers
        super().__init__(self.message)