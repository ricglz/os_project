#!/usr/bin/python3
# -*- coding: utf-8 -*-
import socket

# create a socket object
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# get local machine ip and assign port
host = socket.gethostname()
port = 9999

# connection to hostname on the port.
s.connect((host, port))

# Wait for message to be received from the server
response = s.recv(1024).decode('utf-8')
print(response)

while True:
    msg2 = input()

    s.send(msg2.encode('utf-8'))
