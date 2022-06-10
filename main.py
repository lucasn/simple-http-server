import sys
from server import Server

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

if __name__ == '__main__':
    server = Server(port = PORT)
    server.start()