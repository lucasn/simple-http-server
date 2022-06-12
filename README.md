# Simple Web Library :earth_americas:

Esse projeto foi desenvolvido como trabalho da disciplina TI0145 - Redes de Computadores e consiste de uma biblioteca web simples.

### Funcionalidades
- Servidor web embutido
- Suporte à HTTP/1.1
- Suporte à conexões persistentes e não-persistentes
- Mapeamento de endpoints

### Como usar
A utilização da biblioteca é extremamente simplificada. Cada endpoint da aplicação a ser desenvolvida deve ser mapeado para uma função que será chamada quando uma requisição for enviada para esse endpoint. Esse mapeamento deve ser feito utilizando um dicionário, onde a chave é uma tupla (endpoint, request) e o valor é uma referência para a função que deve ser chamada. Observe o exemplo abaixo:

```py
from models import Response
from server import Server

def helloGet(request):
    return Response(message='Hello GET')

def helloPost(request):
    return Response(message='Hello POST')

urls = {
    ('/', 'GET'): hello,
    ('/', 'POST'): helloPost
}

Server(urls).start()
```