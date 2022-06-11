import socket
import threading
from time import sleep
from signal import signal, SIGINT

from models import Request, Response
from exceptions import ServerException
from configs import HOST, PORT



class Server:
    def __init__(self, urls={}, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.urls = urls
        self.socket = None

        signal(SIGINT, self._shutdown)


    def start(self):
        print('Starting server...')
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen()

        print(f'Listenning on port {self.port}')

        while True:
            client, address = self.socket.accept()

            clientHost, clientPort = client.getpeername()

            print(f'Connection accepted: {clientHost}:{clientPort}')

            tr = threading.Thread(target=self.handleConnection, args=(client,))
            tr.daemon = True
            tr.start()


    def _shutdown(self, sig, frame):
        print('Shutting down...')
        self.socket.close()
        quit()


    def handleConnection(self, client):
        message = client.recv(1024).decode('ascii')
        # TODO: add support for max requests
        timeout = self.checkForPersistentConnection(message)

        if timeout == None:
            response = self.handleRequest(client, message)
            client.send(response.encode('ascii'))
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

            handler = self.urls[(request.path, request.method)]
            return handler(request)

        except ServerException as ex:
            return Response(ex.status, ex.statusMessage, ex.message).build()

        except KeyError:
            return Response(status=404, statusMessage='Not Found').build()


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