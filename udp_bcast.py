import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# because of REUSEADDR we can run both server and this on same machine
# otherwise we would get "address already in use"
sock.bind(('0.0.0.0', 4000))

# receiving message (requires bind)
# recvfrom gives (data, addr) == (data, (ip, port))
print(sock.recvfrom(2000))

# sending message
sock.sendto(b'\x00\x04test\x00\x0bhello there!', ('<broadcast>', 4000))

print(sock.recv(2000))  # probably our own message

# put a sender and receiver on two threads, feed `input()` into sender
# and print any `recv`-ed data, and you got yourself a broadcast chat :)
