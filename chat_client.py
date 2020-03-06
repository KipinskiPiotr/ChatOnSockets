import socket, threading, select

server_address = ("127.0.0.1", 9009)
quit_msg = "#Q#"
nick_UDP_msg = '#N#'

nick = input('Type your nick: ')

# TCP socket
TCP_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
TCP_socket.connect(server_address)

# UDP socket
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Send nick and receive confirmation
TCP_socket.send(nick.encode())
print(TCP_socket.recv(1024).decode())
UDP_socket.sendto((nick_UDP_msg + nick).encode(), server_address)
#print(UDP_socket.recv(1024).decode())

def disconnect():
    try:
        TCP_socket.send(quit_msg.encode())
        TCP_socket.close()
        print('Disconnected')
    except OSError:
        print('Socket already closed')

msg_queue = []

interrupted = False

class ReceiveThread(threading.Thread):
    def __init__(self, TCP_socket, UDP_socket):
        threading.Thread.__init__(self)
        self.TCP_socket = TCP_socket
        self.UDP_socket = UDP_socket

    def run(self):
        global interrupted

        inputs = [self.TCP_socket, self.UDP_socket]
        outputs = [self.TCP_socket]
        errors = [self.TCP_socket]

        while True:
            if interrupted:
                disconnect()
                return

            try:
                readable, writable, err = select.select(inputs, outputs, errors, 1)
            except (ValueError, OSError):
                exit()

            for s in readable:
                try:
                    msg = s.recv(1024).decode()
                    if msg == quit_msg:
                        disconnect()
                        interrupted = True
                        return
                    print("\r" + msg)
                    print(nick + ': ', end='', flush=True)
                except OSError:
                    disconnect()

            for s in writable:
                for msg in msg_queue:
                    s.send(msg.encode())
                msg_queue.clear()

            for s in err:
                print('Error occured!')
                disconnect()
                interrupted = True
                return

TCP_socket.setblocking(0)
ReceiveThread(TCP_socket, UDP_socket).start()

while not interrupted:
    try:
        msg = input(nick + ': ')
    except KeyboardInterrupt:
        interrupted = True

    if msg == 'U':
        UDP_socket.sendto('ASCII ART HERE'.encode(), server_address)
    else:
        msg_queue.append(msg)