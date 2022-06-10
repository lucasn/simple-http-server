import socket
import threading
import sys
from time import sleep

HOST = 'localhost'
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
METHODS = ['GET', 'POST']

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.bind((HOST, PORT))

    s.listen()

    print(f'listenning on port {PORT}')

    while True:
        client, address = s.accept()

        print('connection accepted')

        tr = threading.Thread(target=handleConnection, args=(client, address))
        tr.daemon = True
        tr.start()


def handleConnection(client, address):
    message = client.recv(1024).decode('ascii')
    timeout = checkForPersistentConnection(message)
    if timeout == None:
        handleRequest(client, address, message)
        client.close()
        print('connection closed')
    else:
        # TODO: improve this strategy using semaphores
        # Using the shared variable connection status may cause race conditions
        # Using connectionStatus as list because boolean are passed by value in python
        connectionStatus = [True]
        tr = threading.Thread(target=connectionTimeoutCounter, args=(client, timeout, connectionStatus))
        tr.daemon = True
        tr.start()
        while connectionStatus[0]:
            handleRequest(client, address, message)
            message = client.recv(1024).decode('ascii')
        

def connectionTimeoutCounter(client, timeout, connectionStatus):
    sleep(timeout)
    connectionStatus[0] = False
    client.close()
    print('connection closed')

def handleRequest(client, address, message):
    try:
        request = Request(message)

        print(request.path)
        print(request.method)
        print(request.headers)
        print(request.body)

        if request.method == 'GET':
            response = handleGetRequest(request.path)
            client.send(response.encode('ascii'))
        elif request.method == 'POST':
            response = handlePostRequest(request.path, request.body)
            client.send(response.encode('ascii'))
    except ServerException as ex:
        response = Response(ex.status, ex.statusMessage, ex.message).build()
        client.send(response.encode('ascii'))



def checkHttpVersion(requestLine):

    httpVersion = requestLine[2]

    if httpVersion != 'HTTP/1.1':
        raise ServerException(505, 'HTTP Version Not Supported')


def handleGetRequest(path):
    if path == '/':
        path = '/index.html'

    fullPath = './static' + path

    try:
        f = open(fullPath, 'r')
        fileContent = f.read()
        f.close()
        return Response(status=200, statusMessage='OK', message=fileContent).build()
    except:
        raise ServerException(404, 'Not Found')

def handlePostRequest(path, body):

    if path == '/':
        path = '/index.html'

    fullPath = './static' + path

    try:
        f = open(fullPath, 'r')
        fileContent = f.read()
        f.close()
        fileContent = fileContent.split('<body>')
        responseMessage = fileContent[0] + '<body>\n' + body + fileContent[1]
        return Response(status=200, statusMessage='OK', message=responseMessage).build()
    except:
        raise ServerException(404, 'Not Found')


def checkForPersistentConnection(message):
    lines = message.split('\r\n')
    for line in lines:
        # TODO: treat cases where the keep-alives fields are wrong
        if line.find('Keep-Alive') != -1:
            value = line.split(':')[1].strip()
            fields = value.split(',')
            for field in fields:
                if field.find('timeout') != -1:
                    return int(field.split('=')[1])
    return None


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

    def __init__(self, status=None, statusMessage=None, message=None, headers=defaultHeaders):
        self.status = status
        self.statusMessage = statusMessage
        self.message = message
        self.headers = headers
        self.response = None

    def build(self):
        if self.status == None:
            raise Exception('Failed to build response: status is None')

        if self.statusMessage == None:
            raise Exception('Failed to build response: status message is None')


        self.response = f'HTTP/1.1 {self.status} {self.statusMessage}\r\n'
    
        for header in self.headers:
            self.response += header + '\r\n'

        self.response += '\r\n'

        if self.message != None:
            self.response += self.message + '\r\n'

        return self.response

class ServerException(Exception):
    def __init__(self, status, statusMessage, message=None, headers=[]):
        self.status = status
        self.statusMessage = statusMessage
        self.message = message
        self.headers = headers
        super().__init__(self.message)

if __name__ == '__main__':
    main()