#!/usr/bin/python3
# -*- coding: utf-8 -*-
import socket
from sys import stderr, argv
import random
from time import sleep, time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

politica = argv[1]
seed = argv[2]

# Declarar host y puerto a conectarse
host = 'localhost'
port = 10000

# Se conecta con el servidor
s.connect((host, port))

messages = [(0.0, 'RealMemory 2'), (0.1, 'SwapMemory 4'), (0.2, 'PageSize 16'),
            (0.3, 'PoliticaMemory LRM'), (1, 'P 2048 1'), (2, 'A 1 1 0'),
            (3, 'A 33 1 1'), (4, 'P 32 2'), (5, 'A 15 2 0'), (6, 'A 82 1 0'),
            (7, 'L 2'), (8, 'P 32 3'),  (9, 'L 1'),  (10, 'F'),  (11,  'E')]

# Set custom policy for testing
messages[3] = (0.3, f'PoliticaMemory {politica}')

try:
    previous_msg_time = 0.0
    flag = False
    first_time = True
    for m in messages:
        timestamp = float(m[0])
        msg = m[1]
        initial_msg = timestamp < 1.0
        if first_time:
            first_time = False
            this_msg_time = 0.0
            initial_time = time()
            if seed != '0':
                random.seed(int(seed))
        else:
            this_msg_time = timestamp
            if not initial_msg and seed != '0':
                this_msg_time += random.uniform(-1, 1)
                if this_msg_time < 0.0:
                    this_msg_time = timestamp
                if flag:
                    print(f'Randomised: {this_msg_time}', file=stderr)
            if this_msg_time > previous_msg_time:
                sleep_time = this_msg_time - previous_msg_time
                if flag:
                    print(f'Sleeptime: {sleep_time}', file=stderr)
                sleep(sleep_time)
            else:
                this_msg_time = previous_msg_time
        # Imprime a stderr el mensaje que le va a mandar al servidor
        print(f'Cliente manda: {msg}', file=stderr)

        # Manda mensaje al servidor ya codificado
        s.send(msg.encode('utf-8'))

        previous_msg_time = this_msg_time

        # Recibe la respuesta del servidor
        print(f'Cliente recibe: {s.recv(1024).decode("utf-8")}', file=stderr)

        timestamp_1 = time() - initial_time
        if flag:
            print(f'timestamp: {timestamp_1}', file=stderr)
finally:
    print('Cliente cerrando sesion', file=stderr)
    s.close()

if __name__ == '__main__':
    exit(0)
