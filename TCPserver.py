import socket
import threading

bind_ip = "0.0.0.0"
bind_port = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((bind_ip, bind_port))

#set maximum backlog
server.listen(5)

print("[*] Listening on %s:%d" % (bind_ip, bind_port))

def handle_client(client_socket):
    #prints whats recieved
    request = client.socket.recv(1024)
    print("[*] Recieved: %s" % request)

    #sends back packet
    client_socket.send(b"ACK!")
    print(client_socket.getpeername())
    client_socket.close()

while True:
    client, addr = server.accept()

    print("[*] Accepted connection from: %s:%d" % (addr[0], addr[1]))

    client_handler = threading.Thread(target=handle_client, args=(client,))
    client_handler.start()
