import socket, threading, select, struct

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

server_address = ("127.0.0.1", 9009)
quit_msg = "#Q#"
nick_UDP_msg = '#N#'
ascii_art = """
                                                     _:_
                                                    '-.-'
                                           ()      __.'.__
                                        .-:--:-.  |_______|
                                 ()      \____/    \=====/
                                 /\      {====}     )___(
                      (\=,      //\\\\      )__(     /_____\\
      __    |'-'-'|  //  .\    (    )    /____\     |   |
     /  \   |_____| (( \_  \    )__(      |  |      |   |
     \__/    |===|   ))  `\_)  /____\     |  |      |   |
    /____\   |   |  (/     \    |  |      |  |      |   |
     |  |    |   |   | _.-'|    |  |      |  |      |   |
     |__|    )___(    )___(    /____\    /____\    /_____\\
    (====)  (=====)  (=====)  (======)  (======)  (=======)
    }===={  }====={  }====={  }======{  }======{  }======={
jgs(______)(_______)(_______)(________)(________)(_________)"""

nick = input('Type your nick: ')

# TCP socket
TCP_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
TCP_socket.connect(server_address)

# UDP socket
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Multicast socket
MC_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
MC_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
MC_socket.bind(('', MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
MC_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


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
    def __init__(self, TCP_socket, UDP_socket, MC_socket):
        threading.Thread.__init__(self)
        self.TCP_socket = TCP_socket
        self.UDP_socket = UDP_socket
        self.MC_socket = MC_socket

    def run(self):
        global interrupted

        inputs = [self.TCP_socket, self.UDP_socket, self.MC_socket]
        outputs = [self.TCP_socket]
        errors = [self.TCP_socket]

        while True:
            if interrupted:
                disconnect()
                return

            try:
                readable, writable, err = select.select(inputs, outputs, errors, 1)
            except (ValueError, OSError):
                break

            for s in readable:
                try:
                    msg = s.recv(1024).decode()
                except OSError:
                    disconnect()

                if s is self.MC_socket:
                    if msg[:len(nick) + 1] == nick + ':':
                        continue
            
                if msg == quit_msg:
                    disconnect()
                    interrupted = True
                    return
                
                if len(msg) < len(nick) + 2:
                    print("\r" + msg + ' ' * (len(nick) + 2 - len(msg)))
                else:
                    print("\r" + msg)
                print(nick + ': ', end='', flush=True)

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
ReceiveThread(TCP_socket, UDP_socket, MC_socket).start()

while not interrupted:
    try:
        msg = input(nick + ': ')
    except KeyboardInterrupt:
        interrupted = True

    if msg == 'U':
        UDP_socket.sendto(ascii_art.encode(), server_address)
    elif msg == 'M':
        UDP_socket.sendto((nick + ': ' + ascii_art).encode(), (MCAST_GRP, MCAST_PORT))
    else:
        msg_queue.append(msg)