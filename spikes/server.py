import socket

address = ("192.168.0.155", 5005)
# address = ("localhost", 5005)
# address = ("192.168.0.152", 5005)

soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
# soc.bind(address)
print(f'Sending to {address[0]}:{address[1]}')

while True:
    try:
        msg = input("> ")
        soc.sendto(bytes(msg, 'utf-8'), address)
    except KeyboardInterrupt:
        soc.sendto(b'Bye', address)
        break

soc.close()
