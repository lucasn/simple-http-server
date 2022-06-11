from models import Response
from server import Server

def hello(request):
    return Response(message='Hello').build()

def helloPost(request):
    return Response(message='Hello POST').build()

urls = {
    ('/', 'GET'): hello,
    ('/', 'POST'): helloPost
}

Server(urls).start()