#!/usr/bin/python3
# -*- coding: utf-8 -*-
import socket
import sys
import json
from math import ceil

clientsocket = None
cont = True
params = {}
swaps = []
pages = []
processes = {}


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
        params['PageSize'] = float(words[1]) / 1024
        params['numPages'] = int(params['RealMemory'] / params['PageSize'])
        params['numSwapPages'] = int(params['SwapMemory'] / params['PageSize'])
        initSwap()
        initPages()
        clientsocket.send('Asignando tamaño de página de {} bytes'.
                          format(words[1]).encode('utf-8'))
    elif words[0] == 'P':
        size = float(words[1])
        pid = int(words[2])
        createProcess(size, pid)

        clientsocket.send('Cargando proceso {} con un tamaño de {} bytes'.
                          format(words[2], words[1]).encode('utf-8'))
    elif words[0] == 'A':
        v_memory = int(words[1])
        pid = int(words[2])
        modified = bool(int(words[3]))
        accessMemory(v_memory, pid, modified)
        clientsocket.send('''Accesando memoria virtual {} de proceso {} y es
                              modificable {}'''.
                          format(words[1], words[2], words[3]).encode('utf-8'))
    elif words[0] == 'L':
        pid = int(words[1])
        createProcess(pid)

        clientsocket.send('Liberando información de proceso {}'.
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
        swaps.append({'pid': -1})


def initPages():
    for i in range(0, params['numPages']):
        pages.append({'pid': -1})


def createProcess(size, pid):
    psize = size / params['PageSize'] * 1024
    processes[pid] = {
        'pid': pid, 'size': size, 'psize': ceil(psize), 'pageFault': False
    }


def accessMemory(v, pid, modified):
    res = -1
    bytePageSize = params['PageSize'] * 1024
    p = int(v / bytePageSize)
    d = v % bytePageSize
    pageFrame = searchPage(pid, p, True)

    if v > processes[pid]['size']:
        clientsocket.sendall('Direccion {} fuera de proceso. Se ignora'.
                             format(str(v)).encode('utf-8'))

    if pageFrame != -1:
        res = int(pageFrame * bytePageSize + d)
        clientsocket.sendall('Dirección física de {}: {}'.
                             format(str(v), str(res)).encode('utf-8'))
    else:
        if searchPage(pid, p, False) != -1:
            removeFromSwap()

        clientsocket.sendall('Page fault'.encode('utf-8'))

    return res


def searchPage(pid, page, memoryReal=False):
    array = pages if memoryReal else swaps

    index = 0
    for elem in array:
        if elem['pid'] == pid and elem['page'] == page:
            return index
        index = index + 1
    return -1


def removeFromSwap(pid, page):
    index = 0
    while swaps[index]['pid'] != pid or swaps[index]['page'] != page:
        index = index + 1

    swaps[index]['pid'] = -1


def killProcess(pid):
    for page in pages:
        if page['pid'] == pid:
            page['pid'] = -1
    for swap in swaps:
        if swap['pid'] == pid:
            page['pid'] = -1


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
