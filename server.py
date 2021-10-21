import socket
import sys
import threading
from base64 import b64decode
import time
import struct

# port that we listen on, and they have to connect to
CFG_TCP_PORT_LISTEN = 2000

# port that we dial back on, and they have to listen on
# different from previous for simplicity sake
CFG_TCP_PORT_DIALBACK = 2001

# port for UDP direct messages, everyone should send to this port
# we reply to wherever we got the message from
CFG_UDP_PORT_LISTEN = 3000

# port for UDP broadcast messages, everyone should
# listen on and send to this port **with broadcast**
CFG_UDP_PORT_BCAST = 4000
# CFG_UDP_ADDR_BCAST = '10.0.11.255'

CFG_LISTEN_ADDR = '0.0.0.0'

CFG_BUFFER_SIZE = 2048
CFG_BCAST_TIME = 5

TCP_DIAL_BACK_DATA = [
    (0, 'Did you ever hear the tragedy of Darth Plagueis The Wise?'),
    (1, 'No?'),
    (0, 'I thought not. It\'s not a story the Jedi would tell you.'),
    (0, 'It\'s a Sith legend.'),
    (0, 'Darth Plagueis was a Dark Lord of the Sith, so powerful and so wise he could use the Force to influence the midichlorians to create life…'),
    (0, 'He had such a knowledge of the dark side that he could even keep the ones he cared about from dying.'),
    (1, 'He could actually save people from death?'),
    (0, 'The dark side of the Force is a pathway to many abilities some consider to be unnatural.'),
    (1, 'What happened to him?'),
    (0, 'He became so powerful… the only thing he was afraid of was losing his power, which eventually, of course, he did.'),
    (0, 'Unfortunately, he taught his apprentice everything he knew, then his apprentice killed him in his sleep.'),
    (0, 'Ironic. He could save others from death, but not himself.'),
    (1, 'Is it possible to learn this power?'),
    (0, 'Not from a Jedi.')
]

TCP_HTTP_DATA = b'SFRUUC8xLjEgMzAxIFJpY2tyb2xsZWQNCkxvY2F0aW9uOiBodHRwczovL3d3dy55b3V0dWJlLmNvbS93YXRjaD92PWRRdzR3OVdnWGNRDQoNCg=='

UDP_PING_MESSAGE = b'\x00\x06Server\x00\x11is anyone there ?'


def spawn(callable, /, *args, **kwargs):
    "Run the given function with given arguments in a new thread"
    t = threading.Thread(target=callable, args=args, kwargs=kwargs)
    t.start()


def tcp_server():
    """Start a TCP server that:
    1. acts as an echo server, replying all the data back to the client that connected
    2. tries to dial back to the same IP & dialback port, to test out their server implementations
    """

    # create a INET STREAM TCP socket
    sv_sock = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)

    # set Reuse Address flag, to remove "address in use" errors when
    # a server crashes
    sv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind to the configured address
    sv_sock.bind((CFG_LISTEN_ADDR, CFG_TCP_PORT_LISTEN))
    # start the listener
    sv_sock.listen()

    while True:
        # accept a client
        cl_sock, cl_addr = sv_sock.accept()
        print(cl_addr, '* TCP connected')
        # handle_client acts as an echo server
        spawn(handle_client_tcp, cl_sock, cl_addr)
        # try_dial_back_tcp does what says on the tin
        spawn(try_dial_back_tcp, cl_addr)


def handle_client_tcp(cl_sock: socket.socket, cl_addr):
    "Handle a client connection, by echoing all the data back to them."
    # buffer holding all data so far
    buf = b''
    while True:
        # read a chunk of data
        data = cl_sock.recv(CFG_BUFFER_SIZE)
        if not data:
            # connection is closed if data == b""
            break

        buf += data
        if buf.startswith(b'GET /'):
            # someone is sending us an HTTP request
            # send them a surprise back
            cl_sock.sendall(b64decode(TCP_HTTP_DATA))
            break

        while b'\r\n' in buf:
            # split on newlines
            line, buf = buf.split(b'\r\n', 1)
            # send a responsem in two parts (to check the correct parsing)
            cl_sock.send(b'You said: ')
            time.sleep(0.1)
            cl_sock.send(line + b'\r\n')
            print(cl_addr, '* TCP data:', line)

    # close the socket nicely
    cl_sock.close()


def try_dial_back_tcp(cl_addr):
    "Connect back to client (dialback) to test their server implementation. Send them a tragedy."
    # create our client socket
    socks = [
        socket.socket(socket.AF_INET, socket.SOCK_STREAM),
        socket.socket(socket.AF_INET, socket.SOCK_STREAM),
    ]
    try:
        for sock in socks:
            # connect to the server
            sock.connect((cl_addr[0], CFG_TCP_PORT_DIALBACK))
        socks[0].send(b'\x00\x09TH35EN4TE')
        socks[1].send(b'\x00\x03AN1')
        # send them the data
        # it is sent in chunks to test if they are properly reading
        for i, part in TCP_DIAL_BACK_DATA:
            part = part.encode()
            l = len(part)
            socks[i].sendall(struct.pack('>H', l) + part)
            time.sleep(0.5)
        # close the socket nicely
        sock.close()
        print(cl_addr, '* DIALBACK successful')
    except ConnectionRefusedError:
        # the tcp server is not implemented yet
        return


def udp_server():
    "Start a udp listener. All datagrams are replied to immediately."
    # start a UDP socket
    sv_sock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind it to the address
    sv_sock.bind((CFG_LISTEN_ADDR, CFG_UDP_PORT_LISTEN))

    while True:
        # no listen / accept in udp - just receive
        # we use `recvfrom` here, so that we also get *who* sent the message
        cl_data, cl_addr = sv_sock.recvfrom(CFG_BUFFER_SIZE)
        print(cl_addr, '* UDP packet: ', cl_data)
        # send the data (on a separate thread, so we don't block)
        spawn(send_udp_resp, sv_sock, cl_addr, cl_data)


def send_udp_resp(sock: socket.socket, addr, data: bytes):
    "Send a udp response."
    try:
        name_len = struct.unpack('>H', data[0:2])[0]
        name = data[2:2+name_len].decode()
        msg_len = struct.unpack('>H', data[2+name_len:2+name_len+2])[0]
        msg = data[2+name_len+2:2+name_len+2+msg_len].decode()

        if len(data) != name_len + msg_len + 4:
            raise ValueError('wrong lengths')

        sv_msg = 'Hi {}, you said: {}'.format(name, msg).encode()
        sv_msg_len = len(sv_msg)

        sv_pl = b'\x00\x06Server' + struct.pack('>H', sv_msg_len) + sv_msg

        # just send them the same message, prefixed with "I got: "
        # we use `sendto` so we specify *who* to send the data to
        sock.sendto(sv_pl, addr)
    except BaseException as e:
        print(addr, '* UDP format error: ', e)
        pass


def udp_broadcast():
    "Listen for, and print, broadcast messages."
    # create the socket
    cl_sock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    cl_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # we need to set the BROADCAST socket option
    cl_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # bind the address so we can receive on it
    cl_sock.bind((CFG_LISTEN_ADDR, CFG_UDP_PORT_BCAST))

    # spawn the periodic broadcast funciton, so we generate some traffic
    #
    # NOTE: we will receive these messages ourselves, since we are broadcasting on the same port
    #       THIS CAN CAUSE INFINITE LOOPS IF WE RESPOND TO THE MESSAGES AUTOMATICALY
    spawn(udp_broadcast_loop, cl_sock)

    while True:
        # when we receive something, print it (if it's not our own)
        data, addr = cl_sock.recvfrom(CFG_BUFFER_SIZE)
        if data != UDP_PING_MESSAGE:
            print(addr, '* BCAST:', data)


def udp_broadcast_loop(cl_sock):
    "Broadcast a packet every 5 seconds."
    while True:
        time.sleep(CFG_BCAST_TIME)
        # the '<broadcast>' is required as address, since
        # python will not set required flags in the
        # underlying `send` C call
        cl_sock.sendto(
            UDP_PING_MESSAGE,
            ('<broadcast>', CFG_UDP_PORT_BCAST)
        )


if __name__ == '__main__':
    try:
        # some of these can be commended out, but there is little need
        # (unless you are running on a potato)
        spawn(tcp_server)
        spawn(udp_server)
        spawn(udp_broadcast)
        time.sleep(2**32)
    except KeyboardInterrupt:
        pass
    except BaseException as e:
        print(' ==================== !! FATAL ERROR !! ====================')
        print(e)
        print(' ==================== !! FATAL ERROR !! ====================')
        sys.exit(1)  # force all threads to die
