from crypt import methods
import socket
import threading

HOST = 'localhost'
PORT = 8080
METHODS = ['GET']

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.bind((HOST, PORT))

    s.listen()

    print(f'listenning on port {PORT}')

    while True:
        client, address = s.accept()

        print('connection accepted')

        tr = threading.Thread(target=handleRequest, args=(client, address))

        tr.start()



def handleRequest(client, address):
    message = client.recv(1024).decode('ascii')
    print(message)
    method, path = decodeHTTP(message)

    if method == 'GET':
        response = handleGetRequest(path)
        client.send(response.encode('ascii'))

    client.close()


def decodeHTTP(message):
    request = message.split('\r\n', 1)

    requestLine = request[0].split(' ')

    if len(requestLine) != 3:
        raise Exception('bad request')

    checkHttpVersion(requestLine)

    path = requestLine[1]
    method = requestLine[0]

    if method not in METHODS:
        raise Exception('bad request')

    return (method, path)


def checkHttpVersion(requestLine):

    httpVersion = requestLine[2]

    if httpVersion != 'HTTP/1.1':
        raise Exception('http version not supported')
        

def handleGetRequest(path):
    fullPath = './static' + path
    
    print(fullPath)

    f = open(fullPath, 'r')
    fileContent = f.read()
    f.close()
    return buildResponse(200, 'OK', fileContent)



def buildResponse(status, statusMessage, message=None):
    message = f'HTTP/1.1 {status} {statusMessage}\r\n' \
               'Server: Lucas\r\n' \
               '\r\n' \
              f'{message}\n'

    return message

if __name__ == '__main__':
    main()