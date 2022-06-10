import socket 
import sys
from time import sleep
from server import Request

HOST = 'localhost'
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((HOST, PORT))

print('Connected')

request = Request(
    path='/',
    method='POST'
)

request.build()

message = request.request

print(message)

s.send(message.encode('ascii'))

response = s.recv(1024).decode('ascii')

print(response)

# sleep(2)

# print('again')
# sleep(1)

# message = 'GET / HTTP/1.1\r\n\r\n'

# s.send(message.encode('ascii'))

# response = s.recv(1024).decode('ascii')

# print(response)

# sleep(10)