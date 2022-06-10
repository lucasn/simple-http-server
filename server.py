import socket
import threading
from time import sleep

from models import Request, Response
from exceptions import ServerException
from configs import HOST, PORT

class Server:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port


    def start(self):
        print('Starting server...')
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen()

        print(f'Listenning on port {self.port}')

        while True:
            client, address = s.accept()

            clientHost, clientPort = client.getpeername()

            print(f'Connection accepted: {clientHost}:{clientPort}')

            tr = threading.Thread(target=self.handleConnection, args=(client,))
            tr.daemon = True
            tr.start()


    def handleConnection(self, client):
        message = client.recv(1024).decode('ascii')
        timeout = self.checkForPersistentConnection(message)

        if timeout == None:
            self.handleRequest(client, message)
            clientHost, clientPort = client.getpeername()
            client.close()
            print(f'connection closed: {clientHost}:{clientPort}')
        else:
            # TODO: improve this strategy using semaphores
            # Using the shared variable connection status may cause race conditions
            # Using connectionStatus as list because boolean are passed by value in python
            connectionStatus = [True]
            tr = threading.Thread(target=self.connectionTimeoutCounter, args=(client, timeout, connectionStatus))
            tr.daemon = True
            tr.start()
            while connectionStatus[0]:
                self.handleRequest(client, message)
                message = client.recv(1024).decode('ascii')
        

    def handleRequest(self, client, message):
        try:
            request = Request(message)

            if request.method == 'GET':
                response = self.handleGetRequest(request.path)
                client.send(response.encode('ascii'))

            elif request.method == 'POST':
                response = self.handlePostRequest(request.path, request.body)
                client.send(response.encode('ascii'))

        except ServerException as ex:
            response = Response(ex.status, ex.statusMessage, ex.message).build()
            client.send(response.encode('ascii'))


    def handleGetRequest(self, path):
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


    def handlePostRequest(self, path, body):
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


    def connectionTimeoutCounter(self, client, timeout, connectionStatus):
        sleep(timeout)
        clientHost, clientPort = client.getpeername()
        connectionStatus[0] = False
        client.close()
        print(f'connection closed: {clientHost}:{clientPort}')
        


    def checkForPersistentConnection(self, message):
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