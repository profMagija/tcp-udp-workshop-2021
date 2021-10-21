import socket

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
soc.connect(('127.0.0.1', 2000))

while True:
    # input and send with terminator
    line = input()
    soc.sendall(line.encode() + b'\r\n')

    # keep reading until we see the terminator
    buf = b''
    while not buf.endswith(b'\r\n'):
        buf += soc.recv(1024)

    # print, without \r\n
    print(buf[:-2].decode())
