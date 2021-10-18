import socket

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
soc.connect(('127.0.0.1', 2000))

soc.send(b'hello there')
print(soc.recv(1024).decode())