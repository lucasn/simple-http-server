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
            # Using connectionStatus as list because boolean are passed by value in python
            connectionStatus = [True]
            mutex = threading.Lock()
            tr = threading.Thread(target=self.connectionTimeoutCounter, args=(client, timeout, connectionStatus, mutex))
            tr.daemon = True
            tr.start()
            while connectionStatus[0]:
                response = self.handleRequest(client, message)
                with mutex:
                    if connectionStatus[0]:
                        client.send(response.encode('ascii'))
                message = client.recv(1024).decode('ascii')
        

    def handleRequest(self, client, message):
        try:
            request = Request(message)

            if request.method == 'GET':
                response = self.handleGetRequest(request.path)

            elif request.method == 'POST':
                response = self.handlePostRequest(request.path, request.body)

            return response

        except ServerException as ex:
            return Response(ex.status, ex.statusMessage, ex.message).build()


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


    def connectionTimeoutCounter(self, client, timeout, connectionStatus, mutex):
        sleep(timeout)
        clientHost, clientPort = client.getpeername()
        with mutex:
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