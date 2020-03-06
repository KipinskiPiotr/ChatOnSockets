import socket, threading, select

server_address = ("127.0.0.1", 9009)
quit_msg = "#Q#"

nick = input('Type your nick: ')

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect(server_address)
socket.send(nick.encode())
print(socket.recv(1024).decode())

def disconnect():
    try:
        socket.send(quit_msg.encode())
        socket.close()
        print('Disconnected')
    except OSError:
        print('Socket already closed')

msg_queue = []
inputs = [socket]
outputs = [socket]
errors = [socket]

interrupted = False

class ReceiveThread(threading.Thread):
    def __init__(self, client_socket):
        threading.Thread.__init__(self)
        self.socket = socket

    def run(self):
        global interrupted
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

socket.setblocking(0)
ReceiveThread(socket).start()

while not interrupted:
    try:
        msg = input(nick + ': ')
    except KeyboardInterrupt:
        interrupted = True

    msg_queue.append(msg)