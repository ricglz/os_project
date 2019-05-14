#!/usr/bin/python3
# -*- coding: utf-8 -*-
import socket
import sys

clientsocket = None
cont = True


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
    if 'LRM' in words and 'MRM' in words:
        clientsocket.send('Política LRM y MRM recibidas')
    elif words[0] == 'RealMemory':
        clientsocket.send('Liberando página de proceso {}'.format(words[1]))
    elif words[0] == 'SwapMemory':
        clientsocket.send('Liberando página de proceso {}'.format(words[1]))
    elif words[0] == 'PageSize':
        clientsocket.send('Liberando página de proceso {}'.format(words[1]))
    elif words[0] == 'P':
        clientsocket.send('Cargando proceso {} con un tamaño de {} bytes'.
                          format(words[2], words[1]))
    elif words[0] == 'A':
        clientsocket.send('''Accesando memoria {} de proceso {} y es
                              modificable {}'''.
                          format(words[1], words[2], words[3]))
    elif words[0] == 'L':
        clientsocket.send('Liberando página de proceso {}'.format(words[1]))
    elif words[0] == 'C':
        clientsocket.send('Comentarios')
    elif words[0] == 'F':
        clientsocket.send('Acabar politica')
    elif words[0] == 'E':
        clientsocket.send('Acabar programa')
    else:
        clientsocket.send('Query no valido, intente otra vez')


if __name__ == '__main__':
    clientsocket, addr = start_connection()

    # Print to stderr and sent to client
    msg = 'Se ha hecho la conexión'
    clientsocket.send(msg.encode('utf-8'))
    print(msg)

    try:
        while cont:
            response = clientsocket.recv(1024).decode('utf-8')
            print(response, file=sys.stderr)

            if response:
                analyse_data(response)
            else:
                print('Conexion terminada', file=sys.stderr)
                clientsocket.close()
                sys.exit()

    finally:
        print('Conexion terminada', file=sys.stderr)
