import socket
import threading
import sys
from time import sleep
from configs import HOST, PORT
from models import Request, Response
from exceptions import ServerException

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

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


if __name__ == '__main__':
    main()