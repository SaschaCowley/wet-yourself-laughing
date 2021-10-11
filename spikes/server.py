import socket

address = ("127.0.0.1", 5005)

soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
# soc.bind(address)
print(f'{address[0]}:{address[1]}')

while True:
    try:
        msg = input("> ")
        soc.sendto(bytes(msg, 'utf-8'), address)
    except KeyboardInterrupt:
        soc.sendto(b'Bye', address)
        break

soc.close()
