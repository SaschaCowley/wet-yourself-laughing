import socket
import selectors

address = ("192.168.0.152", 5005)
# address = ("localhost", 5005)
# address = ("192.168.0.152", 5005)

sel = selectors.DefaultSelector()

def recv(sock, mask):
    data, addr = sock.recvfrom(1024)
    print(f'Received {data} from {addr}')

sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
sock.bind(address)

sock.setblocking(False)
sel.register(sock, selectors.EVENT_READ, recv)

print(f'Receiving on {address[0]}:{address[1]}')
while True:
    try:
        events = sel.select(0)
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
    except KeyboardInterrupt:
        break

sock.close()
