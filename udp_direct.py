import socket

# create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# we do not require bind, as server will respond to whatever
# port we are automaticaly assigned
sock.sendto(b'\x00\x03bla\x00\x04haha', ('127.0.0.1', 3000))

# we could also use 'recvfrom' if we
# wanted to know who sent the message
print(sock.recv(2000))
