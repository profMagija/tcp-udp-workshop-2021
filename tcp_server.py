import socket

# create socket
sv_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
# allow address reuse
sv_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# bind to the address and start listening
sv_soc.bind(('0.0.0.0', 2001))
sv_soc.listen()

# accept a single connection
cl_soc, _ = sv_soc.accept()

while True:
    # read data forever
    # NOTE: we are using the *client* socket (result of accept)
    #       *not* the server socket. This is because a single server
    #       can have multiple clients (and writing/reading from a 
    #       server socket will error)
    data = cl_soc.recv(1024)
    if not data:
        break
    print(data.decode())