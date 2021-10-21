import socket
import struct
import threading


def _recv_exact(soc: socket.socket, l: int):
    buf = b''
    while len(buf) < l:
        d = soc.recv(l - len(buf))
        if not d:
            raise ValueError('end of stream')
        buf += d
    return buf


def _recl_longstring(soc: socket.socket):
    name_len = struct.unpack('>H', _recv_exact(soc, 2))[0]
    name = _recv_exact(soc, name_len).decode()
    return name


def handle_client(cl_soc: socket.socket):
    try:
        name = _recl_longstring(cl_soc)
        print(' ==', name, 'commected ==')
        while True:
            data = _recl_longstring(cl_soc)
            print(name + ':', data)
    except:
        pass


def main():
    # create socket
    sv_soc = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    # allow address reuse
    sv_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind to the address and start listening
    sv_soc.bind(('0.0.0.0', 2001))
    sv_soc.listen()

    ping_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ping_soc.connect(('127.0.0.1', 2000))

    while True:
        # accept a single connection
        cl_soc, _ = sv_soc.accept()

        # read data in a new thread
        # NOTE: we are using the *client* socket (result of accept)
        #       *not* the server socket. This is because a single server
        #       can have multiple clients (and writing/reading from a
        #       server socket will error)

        threading.Thread(target=handle_client, args=(cl_soc,)).start()

        # NOTE: doing this:
        #     handle_client(cl_soc)
        # will result in messages being out-of-order


main()
