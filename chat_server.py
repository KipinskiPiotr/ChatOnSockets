import socket, threading, select

server_port = 9009
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('', server_port))
server_socket.listen()

quit_msg = '#Q#'

print('Waiting for clients')
clients = {}

def close_connections():
    for nick, sock in clients.items():
        sock.send(quit_msg.encode())
        sock.close()
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
                readable, writable, err = select.select(inputs, outputs, errors, 5)
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
        for nick, sock in clients.items():
            if nick != self.client_nick:
                sock.send((self.client_nick + ': ' + msg).encode())

    def close_connection(self):
        clients.pop(self.client_nick)
        try:
            self.client_socket.close()
        except:
            print('Already closed')
        print(self.client_nick + ' disconnected!')
        print('Klienci online: ' + str(len(clients)))

inputs = [server_socket]
outputs = [server_socket]
errors = [server_socket]

while True:
    try:
        readable, writable, err = select.select(inputs, outputs, errors, 1)
    except KeyboardInterrupt:
        close_connections()
        server_socket.close()
        break

    for s in readable:
        if s is server_socket:
            connection, client_address = s.accept()
            client_nick = connection.recv(1024).decode()
            print(client_nick + ' connected!')
            clients[client_nick] = connection
            ClientThread(connection, client_nick).start()
            print('Klienci online: ' + str(len(clients)))
        else:
            data = s.recv(1024)

# while True:
#     try:
#         (client_socket, address) = server_socket.accept()
#         client_nick = client_socket.recv(1024).decode()
#     except KeyboardInterrupt:
#         close_connections()
#         break
#     print(client_nick + ' connected!')
#     clients[client_nick] = client_socket
#     ClientThread(client_socket, client_nick).start()
#     print('Klienci online: ' + str(len(clients)))
