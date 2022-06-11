import socket 
import sys
from time import sleep
from models import Request

HOST = 'localhost'
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((HOST, PORT))

print('Connected')

request = Request(
    path='/',
    method='POST',
    headers=['Keep-Alive: timeout=5']
)

message =request.build()

print(message)

s.send(message.encode('ascii'))

response = s.recv(1024).decode('ascii')

print('Receive Response')

sleep(2)

print('again')
sleep(1)

message = Request(
    path='/',
    method='POST'
).build()

print(message)

s.send(message.encode('ascii'))

response = s.recv(1024).decode('ascii')

print('Receive Reponse')

sleep(5)