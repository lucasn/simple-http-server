import socket 


HOST = 'localhost'
PORT = 8080

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((HOST, PORT))

print('Connected')

message = 'GET /index.html HTTP/1.1\r\n'

s.send(message.encode('ascii'))

response = s.recv(1024).decode('ascii')

print(response)

s.close()