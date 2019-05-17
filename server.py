#!/usr/bin/python3
# -*- coding: utf-8 -*-
import socket
import sys
import json
from math import ceil

clientsocket = None
cont = True
params = {}
swap = []
pages = []
processes = []


def start_connection():
    # create a socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # get local machine name
    host = socket.gethostname()
    port = 9999

    # bind to the port
    sock.bind((host, port))

    # Listen to the client
    sock.listen(1)

    return sock.accept()


def analyse_data(time, words):
    if 'LRM' in words and 'MRM' in words and 'PolíticaMemory' in words:
        clientsocket.send('Política LRM y MRM recibidas'.encode('utf-8'))
    elif words[0] == 'RealMemory':
        params['RealMemory'] = float(words[1])
        clientsocket.send('Asignando {} KB de memoria real'.
                          format(words[1]).encode('utf-8'))
    elif words[0] == 'SwapMemory':
        params['SwapMemory'] = float(words[1])
        clientsocket.send('Asignando {} KB de swap memory'.
                          format(words[1]).encode('utf-8'))
    elif words[0] == 'PageSize':
        params['PageSize'] = float(words[1])
        params['numPages'] = int(params['RealMemory'] / params['PageSize'])
        params['numSwapPages'] = int(params['SwapMemory'] / params['PageSize'])
        initSwap()
        initPages()
        clientsocket.send('Asignando tamaño de página de {} bytes'.
                          format(words[1]).encode('utf-8'))
    elif words[0] == 'P':
        createProcess()
        clientsocket.send('Cargando proceso {} con un tamaño de {} bytes'.
                          format(words[2], words[1]).encode('utf-8'))
    elif words[0] == 'A':
        clientsocket.send('''Accesando memoria {} de proceso {} y es
                              modificable {}'''.
                          format(words[1], words[2], words[3]).encode('utf-8'))
    elif words[0] == 'L':
        clientsocket.send('Liberando página de proceso {}'.
                          format(words[1]).encode('utf-8'))
    elif words[0] == 'C':
        clientsocket.send('Comentarios'.encode('utf-8'))
    elif words[0] == 'F':
        clientsocket.send('Acabar politica'.encode('utf-8'))
    elif words[0] == 'E':
        clientsocket.send('Acabar programa'.encode('utf-8'))
    else:
        clientsocket.send('Query no valido, intente otra vez'.encode('utf-8'))


def initSwap():
    for i in range(0, params['numSwapPages']):
        swap.append({'pid': -1})


def initPages():
    for i in range(0, params['numPages']):
        pages.append({'pid': -1})


def createProcess(size, pid):
    psize = size / (params['PageSize'] * 1024)
    processes.append({
        'pid': pid, 'size': size, 'psize': ceil(psize), 'pageFault': False
    })


if __name__ == '__main__':
    clientsocket, addr = start_connection()

    # Print to stderr and sent to client
    msg = 'Se ha hecho la conexión'
    clientsocket.send(msg.encode('utf-8'))
    print(msg, file=sys.stderr)

    try:
        while cont:
            response = json.loads(clientsocket.recv(1024))
            print(response, file=sys.stderr)

            if response:
                analyse_data(response[0], response[1].split())
    except json.decoder.JSONDecodeError:
        print('Conexion terminada', file=sys.stderr)
    finally:
        print('Conexion terminada', file=sys.stderr)
    clientsocket.close()
    sys.exit()
