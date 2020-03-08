import socket, threading, select

address = ('', 9009)
quit_msg = '#Q#'
nick_UDP_msg = '#N#'

# TCP socket
TCP_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
TCP_socket.bind(address)
TCP_socket.listen()

# UDP socket
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_socket.bind(address)

print('Waiting for clients')
clients_connections = {}
clients_UDP = {}

def close_connections():
    for nick, conn in clients_connections.items():
        conn.send(quit_msg.encode())
        conn.close()
        print('Connection with ' + nick + ' closed.')

class ClientThread(threading.Thread):
    def __init__(self, client_socket, client_nick):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.client_nick = client_nick
        self.client_socket.send(("Welcome to chat " + self.client_nick).encode())

    def run(self):
        msg_queue = []
        inputs = [self.client_socket]
        outputs = [self.client_socket]
        errors = [self.client_socket]

        self.client_socket.setblocking(0)

        while True:
            try:
                readable, writable, err = select.select(inputs, outputs, errors, 1)
            except ValueError:
                break

            for s in readable:
                msg = s.recv(1024).decode()
                if msg == quit_msg:
                    self.close_connection()
                    return
                print(msg)
                msg_queue.append(msg)

            for s in writable:
                for msg in msg_queue:
                    self.send_everyone(msg)
                msg_queue.clear()

            for s in err:
                print('Error occured!')
                self.close_connection()
                return
    
    def send_everyone(self, msg):
        for nick, conn in clients_connections.items():
            if nick != self.client_nick:
                conn.send((self.client_nick + ': ' + msg).encode())

    def close_connection(self):
        clients_connections.pop(self.client_nick)
        try:
            self.client_socket.close()
        except:
            print('Already closed')
        print(self.client_nick + ' disconnected!')
        print('Klienci online: ' + str(len(clients_connections)))

inputs = [TCP_socket, UDP_socket]
outputs = [TCP_socket]
errors = [TCP_socket]

while True:
    try:
        readable, writable, err = select.select(inputs, outputs, errors, 1)
    except KeyboardInterrupt:
        close_connections()
        TCP_socket.close()
        UDP_socket.close()
        break

    for s in readable:
        if s is TCP_socket:
            connection, client_address = s.accept()
            client_nick = connection.recv(1024).decode()
            print(client_nick + ' connected!')
            clients_connections[client_nick] = connection
            # Starting new thread for connected client
            ClientThread(connection, client_nick).start()
            print('Klienci online: ' + str(len(clients_connections)))
        else:
            data, address = s.recvfrom(1024)                
            print('Got UDP data from: ' + str(address))
            msg = data.decode()
            if msg[:3] == nick_UDP_msg:
                clients_UDP[msg[3:]] = address
            else:
                nick = ''
                for n, add in clients_UDP.items():
                    if add == address:
                        nick = n
                        break
                for add in clients_UDP.values():
                    if add != address:
                        UDP_socket.sendto((nick + ': ').encode() + data, add)

