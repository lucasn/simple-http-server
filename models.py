from exceptions import ServerException
from configs import METHODS

class Request:
    def __init__(self, rawRequest: str = None, path=None, method=None, headers=[], body=None):
        self.__rawRequest = rawRequest
        self.path = path
        self.method = method
        self.headers = headers
        self.body = body
        self.request = None
        
        if self.__rawRequest != None:
            self.decode()
        else:
            self.build()

    def decode(self):
        request = self.__rawRequest.split('\r\n', 1)
        requestLine = request[0].split(' ')

        if len(requestLine) != 3:
            raise ServerException(400, 'Bad Request')

        self.checkHttpVersion(requestLine)

        self.path = requestLine[1]
        self.method = requestLine[0]

        self.checkMethod()

        restOfRequestMessage = request[1]

        self.splitHeadersAndBody(restOfRequestMessage)


    def build(self):
        if self.path == None:
            raise Exception('Failed to build request: path is None')

        if self.method == None:
            raise Exception('Failed to build request: method is None')
        
        self.request = f'{self.method} {self.path} HTTP/1.1\r\n'

        for header in self.headers:
            self.request += f'{header}\r\n'

        # add empty line to separate headers from body
        # this come from HTTP/1.1 specification
        self.request += '\r\n'

        if self.body != None:
            self.request += self.body + '\r\n'

        return self.request


    def checkHttpVersion(self, requestLine):
        httpVersion = requestLine[2]
        if httpVersion != 'HTTP/1.1':
            raise ServerException(505, 'HTTP Version Not Supported')


    def checkMethod(self):
        if self.method not in METHODS:
            raise ServerException(400, 'Bad Request', 'Method not available')


    def splitHeadersAndBody(self, headersAndBody):
        if len(headersAndBody) > 0:
            actualLine, headersAndBody = headersAndBody.split('\r\n', 1)

            while actualLine != '':
                self.headers.append(actualLine)
                headersAndBody = headersAndBody.split('\r\n', 1)
                actualLine = headersAndBody[0]
                headersAndBody = headersAndBody[1] if len(headersAndBody) > 1 else None

            self.body = headersAndBody

class Response:

    defaultHeaders = ['Server: My Server']

    def __init__(self, status=200, statusMessage='OK', message=None, headers=[]):
        self.status = status
        self.statusMessage = statusMessage
        self.message = message
        self.response = None
        self.headers = []

        for header in Response.defaultHeaders:
            self.headers.append(header)
        
        self.headers += headers

    def build(self):
        if self.status == None:
            raise Exception('Failed to build response: status is None')

        if self.statusMessage == None:
            raise Exception('Failed to build response: status message is None')

        self.headers.append(f'Content-Length: {len(self.message) if self.message != None else 0}')

        self.response = f'HTTP/1.1 {self.status} {self.statusMessage}\r\n'
    
        for header in self.headers:
            self.response += header + '\r\n'

        self.response += '\r\n'

        if self.message != None:
            self.response += self.message + '\r\n'

        return self.response