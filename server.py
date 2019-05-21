#!/usr/bin/python3
# -*- coding: utf-8 -*-
import socket
from time import time
import sys
from math import ceil

clientsocket = None
flag = True
params = {}
swaps = []
pages = []
processes = {}
freePages = 0
arrivTime = 0
words=[]
res = 0
done = 0
timestamp = 0
pageF = 0
p = 0

def start_connection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = ('localhost', 10000)
    print(f'Conectando en la dirección {server_address}', file=sys.stderr)

    sock.bind(server_address)

    sock.listen(1)
    print('Esperando a que el cliente se conecte', file=sys.stderr)

    return sock.accept()


def analyse_data(words):
    global flag, freePages, arrivTime

    arrivTime=time()
    if words[0] == 'PoliticaMemory':
        if words[1] == 'LRM':
            params['LRM'] = True
            clientsocket.send('Política LRM recibida'.encode('utf-8'))
        elif 'MRM':
            params['LRM'] = False
            clientsocket.send('Politica MRM recibida'.encode('utf-8'))
        else:
            clientsocket.send('Query invalido, intentelo otra vez'.
                              encode('utf-8'))
    elif words[0] == 'RealMemory':
        params['RealMemory'] = float(words[1]) * 1024
        clientsocket.send('Asignando {} KB de memoria real'.
                          format(words[1]).encode('utf-8'))
    elif words[0] == 'SwapMemory':
        params['SwapMemory'] = float(words[1]) * 1024
        clientsocket.send('Asignando {} KB de swap memory'.
                          format(words[1]).encode('utf-8'))
    elif words[0] == 'PageSize':
        params['PageSize'] = float(words[1])
        params['numPages'] = int(params['RealMemory'] / params['PageSize'])
        freePages = params['numPages']
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
        showTableF()
        clientsocket.send('Acabando secuencia de datos'.encode('utf-8'))
    elif words[0] == 'E':
        showTableE()
        clientsocket.send('Acabando programa'.encode('utf-8'))
        flag = False
    else:
        clientsocket.send('Query no valido, intente otra vez'.encode('utf-8'))


def initSwap():
    global timestamp
    timestamp = time()
    for i in range(0, params['numSwapPages']):
        swaps.append({'pid': -1, 'lastModified': timestamp})


def initPages():
    global timestamp
    timestamp = time()
    for i in range(0, params['numPages']):
        pages.append({'pid': -1, 'lastModified': timestamp})


def createProcess(size, pid):
    global timestamp, pageF, p
    if size > params['RealMemory']:
        print('El proceso es más grande que la memoria real se ignora',
              file=sys.stderr)
    pagesCount = size / params['PageSize']
    processes[pid] = {
        'pid': pid, 'size': size, 'pagesCount': ceil(pagesCount),
        'pageFault': False
    }
    p = p + 1
    timestamp = time()
    if freePages >= pagesCount:
        fill_pages(pid, pagesCount, timestamp)

    else:
        swap_with_other_process(pid, pagesCount, timestamp)
        pageF = pageF + 1


def fill_pages(pid, pagesCount, timestamp):
    index = 0
    pageNumber = 0
    while index < params['numPages'] and pageNumber < pagesCount:
        if pages[index]['pid'] == -1:
            pages[index]['pid'] = pid
            pages[index]['pageNumber'] = pageNumber
            pages[index]['lastModified'] = timestamp
            pageNumber = pageNumber + 1
        index = index + 1


def swap_with_other_process(pid, pagesCount, timestamp):
    pageNumber = 0
    while pageNumber < pagesCount:
        best_option = get_replacement()
        change_with_swap(pages[best_option])
        pages[best_option]['pid'] = pid
        pages[best_option]['pageNumber'] = pageNumber
        pages[best_option]['lastModified'] = timestamp
        pageNumber = pageNumber + 1


def get_replacement():
    best_option = 0
    best_timestamp = pages[0]['lastModified']
    index = 1
    while index < params['numPages']:
        if (params['LRM'] and
           pages[index]['lastModified'] < best_timestamp):
            best_option = index
            best_timestamp = pages[index]['lastModified']
        elif (not params['LRM'] and
              pages[index]['lastModified'] > best_timestamp):
            best_option = index
            best_timestamp = pages[index]['lastModified']
        index = index + 1
    return best_option


def change_with_swap(page):
    index = 0
    while index < params['numSwapPages']:
        if swaps[index]['pid'] == -1:
            swaps[index] = page
            return


def accessMemory(v, pid, modified):
    global res
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
            replacementFrame = get_replacement()
            replaceWithNewPid(pid, p, replacementFrame)
            pages[replacementFrame]['pid'] = pid
            pages[replacementFrame]['pageNumber'] = pageFrame

        print('Ocurrió un fallo de pagina', file=sys.stderr)


def searchPage(pid, page, realMemory=False):
    array = pages if realMemory else swaps

    index = 0
    for elem in array:
        if elem['pid'] == pid and elem['pageNumber'] == page:
            return index
        index = index + 1

    return -1


def replaceWithNewPid(pid, page, frame):
    index = 0
    while swaps[index]['pid'] != pid or swaps[index]['page'] != page:
        index = index + 1

    swaps[index]['pid'] = pages[frame]['pid']


def killProcess(pid):
    global freePagesm, done
    for page in pages:
        if page['pid'] == pid:
            page['pid'] = -1
            freePages = freePages + 1
    for swap in swaps:
        if swap['pid'] == pid:
            swap['pid'] = -1
    done=done+1


def killAllProcesses():
    global freePages
    for page in pages:
        page['pid'] = -1
    for swap in swaps:
        swap['pid'] = -1
    freePages = params['numPages']


# Funcion que imprime tabla que recibe de parametro: data, numero y anchura de
# columnas. Esta tabla despliega información del conjunto de operaciones para
# una politica
def showTableF(data, cols, wide):
    n, r = divmod(len(data), cols)
    pat = '{{:{}}}'.format(wide)
    line = '\n'.join(pat * cols for _ in range(n))
    last_line = pat * r
    print("Tiempo", "Comando", "Dir. Real", "Memoria Real", "Area Swapping",
          "Terminados")
    print(line.format(*data))
    print(last_line.format(*data[n*cols:]))
    #data = [str(i) for i in range(27)]
    data = [arrivTime, words, res, '-', '-', done]
    print_table(data, 6, 12)
    return


# Esta funcion despliega metricas para cada proceso creado
# (Turnaround=T.salida-T.llegada, #page faults, #swap-ins, #swap-outs, Rendimiento=1-#fallas/#comandos A y TOTALES, rendAvg= 1-(totPageF/totA))
def showTableE():
    turnaround = timestamp-arrivTime
    #rend =

    n, r = divmod(len(data), cols)
    pat = '{{:{}}}'.format(wide)
    line = '\n'.join(pat * cols for _ in range(n))
    last_line = pat * r
    print("Proceso", "Turnaround", "# Page faults", "# Swap-ins",
          "# Swap-outs", "Rendimiento")
    print(line.format(*data), file=sys.stderr)
    print(last_line.format(*data[n*cols:]), file=sys.stderr)
    #data = [str(i) for i in range(27)]
    data = [p, turnaround, pageF, '-', '-', '-']
    p = p+1
    print_table(data, 6, 12)
          file=sys.stderr)
    return


def receive_message():
    response = clientsocket.recv(1024).decode('utf-8')
    print(f'El servidor recibe {response}:', file=sys.stderr)
    return response


if __name__ == '__main__':
    clientsocket, addr = start_connection()

    print('Se ha hecho la conexión', file=sys.stderr)

    try:
        while flag:
            words = receive_message().split()
            analyse_data(words)
    finally:
        print('Servidor cerrando sesión', file=sys.stderr)
        clientsocket.close()
        sys.exit()
