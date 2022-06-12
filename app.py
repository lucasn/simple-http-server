from models import Response
from server import Server

def hello(request):
    return Response(message='Hello')

def helloPost(request):
    return Response(message='Hello POST')

urls = {
    ('/', 'GET'): hello,
    ('/', 'POST'): helloPost
}

Server(urls).start()