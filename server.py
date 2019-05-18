#!/usr/bin/python3
# -*- coding: utf-8 -*-
import socket
import sys
import json
from math import ceil

clientsocket = None
flag = True
params = {}
swaps = []
pages = []
processes = {}
freePages = 0


def start_connection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = (socket.gethostname(), 3000)
    print(f'Conectando en la dirección {server_address}', file=sys.stderr)

    sock.bind(server_address)

    sock.listen(1)
    print('Esperando a que el cliente se conecte', file=sys.stderr)

    return sock.accept()


def analyse_data(time, words):
    global flag, freePages

    if 'LRM' in words and 'MRM' in words and 'PolíticaMemory' in words:
        clientsocket.send('Política LRM y MRM recibidas'.encode('utf-8'))
    elif words[0] == 'RealMemory':
        params['RealMemory'] = float(words[1]) * 1024
        freePages = params['RealMemory']
        clientsocket.send('Asignando {} KB de memoria real'.
                          format(words[1]).encode('utf-8'))
    elif words[0] == 'SwapMemory':
        params['SwapMemory'] = float(words[1]) * 1024
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
        killProcess(pid)

        clientsocket.send('Liberando información de proceso {}'.
                          format(words[1]).encode('utf-8'))
    elif words[0] == 'C':
        clientsocket.send('Haciendo comentarios'.encode('utf-8'))
    elif words[0] == 'F':
        killAllProcesses()
        clientsocket.send('Acabando secuencia de datos'.encode('utf-8'))
    elif words[0] == 'E':
        clientsocket.send('Acabando programa'.encode('utf-8'))
        flag = False
    else:
        clientsocket.send('Query no valido, intente otra vez'.encode('utf-8'))


def initSwap():
    for i in range(0, params['numSwapPages']):
        swaps.append({'pid': -1})


def initPages():
    for i in range(0, params['numPages']):
        pages.append({'pid': -1})


def createProcess(size, pid):
    if size > params['RealMemory']:
        print('El proceso es más grande que la memoria real se ignora',
              file=sys.stderr)
    pagesCount = size / params['PageSize']
    processes[pid] = {
        'pid': pid, 'size': size, 'pagesCount': ceil(pagesCount),
        'pageFault': False
    }
    if freePages >= pagesCount:
        fill_pages(0, pid, pagesCount)
    else:
        swap_with_other_process()


def fill_pages(pageNumber, pid, pagesCount):
    index = 0
    while index < params['numPages'] and pageNumber < pagesCount:
        if pages[index]['pid'] == -1:
            pages[index]['pid'] = pid
            pages[index]['pageNumber'] = pageNumber
            pageNumber = pageNumber + 1
        index = index + 1


def swap_with_other_process():
    return


def accessMemory(v, pid, modified):
    res = -1
    if v > processes[pid]['size']:
        print(f'''Direccion virtual {str(v)} fuera de proceso, se ignorara''',
              file=sys.stderr)
        return

    p = int(v / params['PageSize'])
    d = v % params['PageSize']
    pageFrame = searchPage(pid, p, True)

    if pageFrame != -1:
        res = int(pageFrame * params['PageSize'] + d)
        print(f'''Dirección física de {str(v)}: {str(res)}''',
              file=sys.stderr)
    else:
        if searchPage(pid, p) != -1:
            removeFromSwap(pid, p)

        print('Ocurrió un fallo de pagina', file=sys.stderr)


def searchPage(pid, page, realMemory=False):
    array = pages if realMemory else swaps

    index = 0
    for elem in array:
        if elem['pid'] == pid and elem['pageNumber'] == page:
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
            swap['pid'] = -1


def receive_message():
    response = json.loads(clientsocket.recv(1024).decode('utf-8'))
    print(f'El servidor recibe {response}:', file=sys.stderr)
    return response


def killAllProcesses():
    for page in pages:
        page['pid'] = -1
    for swap in swaps:
        swap['pid'] = -1


if __name__ == '__main__':
    clientsocket, addr = start_connection()

    msg = 'Se ha hecho la conexión'
    clientsocket.send(msg.encode('utf-8'))
    print(msg, file=sys.stderr)

    try:
        while flag:
            response = receive_message()
            words = response[1].split()
            analyse_data(response[0], words)
    finally:
        print('Servidor cerrando sesión', file=sys.stderr)
        clientsocket.close()
        sys.exit()
