import socket

address = ("127.0.0.1", 5005)

soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
soc.bind(address)
print(f'Receiving from {address[0]}:{address[1]}')

while True:
    try:
        data, addr = soc.recvfrom(1024)
        print(f'Received {data}\n{addr}\n\n')
    except KeyboardInterrupt:
        break

soc.close()
