from operator import rshift
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
        method, path, headers, body = decodeHTTP(message)

        if method == 'GET':
            response = handleGetRequest(path)
            client.send(response.encode('ascii'))
        elif method == 'POST':
            response = handlePostRequest(path, body)
            client.send(response.encode('ascii'))
    except ServerException as ex:
        response = buildResponse(ex.status, ex.statusMessage, ex.message)
        client.send(response.encode('ascii'))


def decodeHTTP(message):
    request = message.split('\r\n', 1)

    requestLine = request[0].split(' ')

    if len(requestLine) != 3:
        raise ServerException(400, 'Bad Request')

    checkHttpVersion(requestLine)

    path = requestLine[1]
    method = requestLine[0]

    if method not in METHODS:
        raise ServerException(400, 'Bad Request', 'Method not available')

    restOfRequestMessage = request[1]

    actualLine, restOfRequestMessage = restOfRequestMessage.split('\r\n', 1)

    headers = []
    while actualLine != '':
        headers.append(actualLine)
        restOfRequestMessage = restOfRequestMessage.split('\r\n', 1)
        actualLine = restOfRequestMessage[0]
        restOfRequestMessage = restOfRequestMessage[1] if len(restOfRequestMessage) > 1 else None

    body = restOfRequestMessage

    return (method, path, headers, body)


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
        return buildResponse(200, 'OK', fileContent)
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
        return buildResponse(200, 'OK', responseMessage)
    except:
        raise ServerException(404, 'Not Found')


def buildResponse(status, statusMessage, message=None):
    response = f'HTTP/1.1 {status} {statusMessage}\r\n' \
               'Server: Lucas\r\n' \
               '\r\n'
    
    if message != None:
        response += f'{message}\n'

    return response

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


class ServerException(Exception):
    def __init__(self, status, statusMessage, message=None):
        self.status = status
        self.statusMessage = statusMessage
        self.message = message
        super().__init__(self.message)

if __name__ == '__main__':
    main()