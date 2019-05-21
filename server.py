"""
    Autores:
        Ricardo Gonzales A01338143
        Manuel Torres Magdaleno A01066869
        Martha Elena García Ramos A01139413
        Este programa es un simulador de memoria virtual paginada que recibe datos del servidor sobre atributos como el tamaño de memoria real, tamaño de area de swapping y tamaño de página. El programa cliente envia al servidor un conjunto de peticiones para cargar un proceso a memoria, accesar memoria y liberar memoria.
            Para verificar el manejo correcto de la memoria, el servidor deberá desplegar periódicamente el estado de los marcos de página reales y “swappeados” al área de swapping y otros datos como metricas de rendimiento, tiempo de ejecución, etc.
            Al terminan un conjunto de instrucciones, el programa debe aceptar otro tipo de politica para reemplazo de paginas.
    
"""


#!/usr/bin/python3
# -*- coding: utf-8 -*-
#importa bibliotecas para conexión de cliente servidor y utilizar variables de tiempo
import socket
from time import time
import sys
from math import ceil

#variables globales
clientsocket = None #para realizar conexion con socket del cliente
flag = True #bandera para validar cuando programa deba estar ejecutando
params = {} #inputs de cliente
swaps = [] #registra swaps
pages = [] #registra paginas de memoria
processes = {} #registra procesos de input del cliente
freePages = 0 #reistra cantidad de paginas libres en memoria
arrivTime = 0 #registra tiempo de llegada de cada input del cliente
words=[] #inputs del cliente
res = 0 #direccion real
done = 0 #contador de procesos terminados
timestamp = 0 #tiempo de salida
pageF = 0 #contador de page faults
p = 0 #contador de procesos creados

#funcion que crea una conexión entre cliente y servidor, envia mensajes comprobando estatus de operación
def start_connection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = ('localhost', 10000)
    print(f'Conectando en la dirección {server_address}', file=sys.stderr)

    sock.bind(server_address)

    sock.listen(1)
    print('Esperando a que el cliente se conecte', file=sys.stderr)

    return sock.accept()

#funcion que guarda inputs de cliente y llama a funciones correspondientes para realizar comandos que cliente desea
def analyse_data(words):
    global flag, freePages, arrivTime #variables globales utilziadas

    arrivTime=time() #tiempo de llegada de input de cliente
    if words[0] == 'PoliticaMemory': #verifica que tipo de politica esta mandando el cliente
        if words[1] == 'LRM':
            params['LRM'] = True
            clientsocket.send('Política LRM recibida'.encode('utf-8')) #confirma input recibido
        elif 'MRM':
            params['LRM'] = False
            clientsocket.send('Politica MRM recibida'.encode('utf-8')) #confirma input recibido
        else:
            clientsocket.send('Query invalido, intentelo otra vez'. #marca error al no ser aceptada la politica deseada del cliente
                              encode('utf-8'))
    elif words[0] == 'RealMemory': #recibe parametros de memoria real del cliente
        params['RealMemory'] = float(words[1]) * 1024 #convierte de kb a bytes
        clientsocket.send('Asignando {} KB de memoria real'. #confirma input recibido
                          format(words[1]).encode('utf-8'))
    elif words[0] == 'SwapMemory': #recibe parametros de memoria de swap del cliente
        params['SwapMemory'] = float(words[1]) * 1024 #convierte de kb a bytes
        clientsocket.send('Asignando {} KB de swap memory'.
                          format(words[1]).encode('utf-8')) #confirma input recibido
    elif words[0] == 'PageSize': #recibe parametro de tamaño de pagina
        params['PageSize'] = float(words[1]) #guarda dato
        params['numPages'] = int(params['RealMemory'] / params['PageSize']) #calcula cantidad de paginas
        freePages = params['numPages'] #inicializa numero de paginas libres igual a numero de paginas
        params['numSwapPages'] = int(params['SwapMemory'] / params['PageSize']) #calcula cantidad de paginas de swap
        initSwap() #llama a funcion que inicaliza memoria de swap
        initPages() #llama a funcion que inicaliza memoria
        clientsocket.send('Asignando tamaño de página de {} bytes'.
                          format(words[1]).encode('utf-8')) #confirma asignacion de tamaño pag
    elif words[0] == 'P': #si cliente desea cargar un proceso...
        size = float(words[1]) #guarda tamaño de proceso en bytes
        pid = int(words[2]) #guarda id de proceso
        createProcess(size, pid) #manda llamar funcion que crea el proceso, con atributos como parametros

        clientsocket.send('Cargando proceso {} con un tamaño de {} bytes'.
                          format(words[2], words[1]).encode('utf-8')) #notifica a cliente que realiza la operacion
    elif words[0] == 'A': #si cliente desea accesar a memoria...
        v_memory = int(words[1]) #guarda direccion virtual
        pid = int(words[2]) #guarda id de proceso
        modified = bool(int(words[3])) #guarda bit de modificacion para saber si modifica(1) o solo lee(0)
        accessMemory(v_memory, pid, modified) #llama a funcion que accesa memoria con atributos como parametros
        clientsocket.send('''Accesando memoria virtual {} de proceso {} y es
                              modificable {}'''.
                          format(words[1], words[2], words[3]).encode('utf-8')) #notifica a cliente que realiza operacion
    elif words[0] == 'L': #si cliente desea liberar un proceso...
        pid = int(words[1]) #guarda id de proceso a liberar
        killProcess(pid) #llama a funcion que mata un proceso segun su id como parametro

        clientsocket.send('Liberando información de proceso {}'.
                          format(words[1]).encode('utf-8')) #notifica a cliente que realiza operacion
    elif words[0] == 'C':
        clientsocket.send('Haciendo comentarios'.encode('utf-8')) #notifica a cliente que realiza operacion
    elif words[0] == 'F': #si el cliente desea terminar un conjunto de comandos
        killAllProcesses() #llama a funcion que termina todos los procesos
        showTableF() #muestra tabla con informacion del conjunto de comandos
        clientsocket.send('Acabando secuencia de datos'.encode('utf-8')) #notifica a cliente que realiza operacion
    elif words[0] == 'E': #si cliente desea terminar programa...
        showTableE() #muestra tabla con metricas del programa
        clientsocket.send('Acabando programa'.encode('utf-8')) #notifica a cliente que realiza operacion
        flag = False #cambia valor de flag para que termine programa
    else:
        clientsocket.send('Query no valido, intente otra vez'.encode('utf-8')) #notifica a cliente que el input no es valido

#funcion que inicializa memoria de swap
def initSwap():
    global timestamp
    timestamp = time() #variable que usa biblioteca time para calcular tiempo de ultima vez que se modifico
    for i in range(0, params['numSwapPages']): #con un ciclo inicializa segun el numero de paginas de memoria swap
        swaps.append({'pid': -1, 'lastModified': timestamp}) #registra timestamp de ultima vez que fue modificado

#funcion que inicializa memoria de paginacion
def initPages():
    global timestamp
    timestamp = time() #variable que usa biblioteca time para calcular tiempo de ultima vez que se modifico
    for i in range(0, params['numPages']): #con un ciclo inicializa segun el numero de paginas de memoria
        pages.append({'pid': -1, 'lastModified': timestamp}) #registra timestamp de ultima vez que fue modificado

#funcion que crea proceso segun su tamaño y id
def createProcess(size, pid):
    global timestamp, pageF, p #variables globales
    if size > params['RealMemory']: #si el tamaño es mayor que la memoria real, notifica cliente
        print('El proceso es más grande que la memoria real se ignora',
              file=sys.stderr)
    pagesCount = size / params['PageSize'] #calcula numero de paginas
    processes[pid] = {
        'pid': pid, 'size': size, 'pagesCount': ceil(pagesCount),
        'pageFault': False
    } #inicializa arrelo processes con atributos correspondientes
    p = p + 1 #contador de numeo de procesos creados
    timestamp = time() #calcula tiempo en que fue creado un proceso
    if freePages >= pagesCount: #si las paginas necesarias para guardar el proceso en memoria es menor a el numero de paginas libres
        fill_pages(pid, pagesCount, timestamp) #llama funcion para llenar paginas

    else: #si no existen painas libres que guarden las paginas necesarias del proceso
        swap_with_other_process(pid, pagesCount, timestamp) #llama funcion donde intercambia entre memoria swap y memoria real
        pageF = pageF + 1 #aumenta contador de page faults

#funcion que llena paginas de un proceso en memoria real
def fill_pages(pid, pagesCount, timestamp):
    index = 0 #contador de paginas llenadas
    pageNumber = 0 #contador de numero de paginas
    while index < params['numPages'] and pageNumber < pagesCount: #ciclo que mientras el contador sea menor a la cantidad de paginas del rpcoeso y el numero de paginas menor a la cantidad de paginas de memoria, asigna información
        if pages[index]['pid'] == -1:
            pages[index]['pid'] = pid
            pages[index]['pageNumber'] = pageNumber
            pages[index]['lastModified'] = timestamp
            pageNumber = pageNumber + 1 #aumenta contador
        index = index + 1 #aumenta contador

#Funcion que checa mediante timestamp y la posición en la que se encuentra en el arreglo la manera en que realiza el reemplazo de paginas
def swap_with_other_process(pid, pagesCount, timestamp):
    pageNumber = 0
    while pageNumber < pagesCount: #mientras que quepan la cantidad de paginas en memoria
        best_option = get_replacement() #llama a funcion que reemplaza según MRM o LRM
        change_with_swap(pages[best_option]) #llama a funcion que realiza swaps
        #en arreglo pages asgina data segun lo que regresa funcion get_replacement
        pages[best_option]['pid'] = pid
        pages[best_option]['pageNumber'] = pageNumber
        pages[best_option]['lastModified'] = timestamp
        pageNumber = pageNumber + 1 #aumenta contador

#Funcion que regresa la mejor opcion para reemplazar según la politica
def get_replacement():
    best_option = 0 #inicializa variable donde guardara resultado a regresar, simboliza que politica utilzar
    best_timestamp = pages[0]['lastModified'] #segun el timestamp(FIFO) regresa que pagina se debe elegir en la politica
    index = 1 #contador
    while index < params['numPages']: #ciclo para definir valores de best_option y best_timestamp segun sea la politica
        if (params['LRM'] and pages[index]['lastModified'] < best_timestamp): #si la politica es LRM y la pagina es menor al best_timestamp
            #se asignan valores a variables
            best_option = index
            best_timestamp = pages[index]['lastModified']
        elif (not params['LRM'] and pages[index]['lastModified'] > best_timestamp): #si la politica es MRM y la pagina es mayor al best_timestamp
            #se asignan valores a variables
            best_option = index
            best_timestamp = pages[index]['lastModified']
        index = index + 1 #incrementa contador
    return best_option #regresa

#funcion que realiza swaps, segun la pagina
def change_with_swap(page):
    index = 0 #contador
    while index < params['numSwapPages']: #mientras contador sea menor que numero de paginas de swap
        if swaps[index]['pid'] == -1: #si esta libre
            swaps[index] = page #realiza el cambio
            return

#funcion que acceso memoria segun la direccion virtual, id del proceso y el bit de modificacion
def accessMemory(v, pid, modified):
    global res #variable que guarda valor de direccion real
    res = -1
    if v > processes[pid]['size']: #si la direccion virtual es mayor que el tamaño, se ignora y notifica como error al cliente
        print(f'''Direccion virtual {str(v)} fuera de proceso, se ignorara''',
              file=sys.stderr)
        return #termina funcion

    p = int(v / params['PageSize']) #pagina
    d = v % params['PageSize'] #desplazamiento
    pageFrame = searchPage(pid, p, True) #llama funcion que busca pagina segun su id para calcular su marco de pagina

    if pageFrame != -1:
        res = int(pageFrame * params['PageSize'] + d) #direccion real es marco de pagina
        print(f'''Dirección física de {str(v)}: {str(res)}''', #notifica a cliente la direccion fisica
              file=sys.stderr)
    else: #si pageFrame es -1
        if searchPage(pid, p) != -1: #si el resultado obtenido en funcion searchPage es diferente a -1
            replacementFrame = get_replacement() #se inicializa marco de pagina de reemplazo
            replaceWithNewPid(pid, p, replacementFrame) #se llama a funcion que reemplaza con un nuevo id del proceso
            pages[replacementFrame]['pid'] = pid #se asigna a pages el id segun el marco de reemplazo
            pages[replacementFrame]['pageNumber'] = pageFrame #se asigna a pages el marco de pagina segun el marco de reemplazo

        print('Ocurrió un fallo de pagina', file=sys.stderr) #notifica al cliente fallo de pagina

# funcion que busca pagina en memoria segun su id
def searchPage(pid, page, realMemory=False):
    array = pages if realMemory else swaps #arreglo con pagenas de real memoria y swaps

    index = 0 #contador
    for elem in array:
        if elem['pid'] == pid and elem['pageNumber'] == page:
            return index #regresa contador con valor de numero de pagina que se encontro la del parametro
        index = index + 1 #aumenta contador
    return -1

# funcion que reemplaza area de swap segun el id del proceso
def replaceWithNewPid(pid, page, frame):
    index = 0 #contador
    #mientras que swaps tenga un id o pagina diferente
    while swaps[index]['pid'] != pid or swaps[index]['page'] != page:
        index = index + 1 # se incrementa contador
    swaps[index]['pid'] = pages[frame]['pid'] #se hace swap con arreglo pages, segun el id

#funcion que libera un proceso segun su id
def killProcess(pid):
    global freePagesm, done #variables globales
    # ciclo que libera paginas al inicializar en -1
    for page in pages:
        if page['pid'] == pid:
            page['pid'] = -1
            freePages = freePages + 1
    # ciclo que libera area de swaps al inicializar en -1
    for swap in swaps:
        if swap['pid'] == pid:
            swap['pid'] = -1
    done=done+1 #contador de procesos terminados

#funcion que termina todos los procesos
def killAllProcesses():
    global freePages #variable global
    # ciclo que libera paginas al inicializar en -1
    for page in pages:
        page['pid'] = -1
    # ciclo que libera area de swaps al inicializar en -1
    for swap in swaps:
        swap['pid'] = -1
    #asigna paginas libres segun lo obtenido como parametro
    freePages = params['numPages']


# Funcion que imprime tabla que recibe de parametro: data, numero y anchura de
# columnas. Esta tabla despliega información del conjunto de operaciones para
# una politica
def showTableF(data, cols, wide):
    cols= 6
    wide = 12
    #se define formato de columnas y renglones
    n, r = divmod(len(data), cols)
    pat = '{{:{}}}'.format(wide)
    line = '\n'.join(pat * cols for _ in range(n))
    last_line = pat * r
    #imprime header
    print("Tiempo", "Comando", "Dir. Real", "Memoria Real", "Area Swapping",
          "Terminados")
    data = [arrivTime, words, res, '-', '-', done]
    #imprime data segun formato
    print(line.format(*data))
    print(last_line.format(*data[n*cols:]))
    print_table()
    return


# Esta funcion despliega metricas para cada proceso creado
# (Turnaround=T.salida-T.llegada, #page faults, #swap-ins, #swap-outs, Rendimiento=1-#fallas/#comandos A y TOTALES, rendAvg= 1-(totPageF/totA))
def showTableE():
    cols= 6
    wide = 12
    turnaround = timestamp-arrivTime
    #se define formato de columnas y renglones
    n, r = divmod(len(data), cols)
    pat = '{{:{}}}'.format(wide)
    line = '\n'.join(pat * cols for _ in range(n))
    last_line = pat * r
    #imprime header
    print("Proceso", "Turnaround", "# Page faults", "# Swap-ins",
          "# Swap-outs", "Rendimiento")
    data = [p, turnaround, pageF, '-', '-', '-']
    print(line.format(*data), file=sys.stderr)
    print(last_line.format(*data[n*cols:]), file=sys.stderr)
    p = p+1
    print_table()
    return

#funcion que recibe mensaje de cliente
def receive_message():
    response = clientsocket.recv(1024).decode('utf-8')
    print(f'El servidor recibe {response}:', file=sys.stderr)
    return response

#funcion principal
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
