import socket

target_host = "127.0.0.1"
target_port = 80

#notice the lack of a call to connect() due to UDP being a connectionless protocol

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

client.sendto(b"randomdatahere",(target_host, target_port))

data, addr = client.recvfrom(4096)

client.close()

print(data)
