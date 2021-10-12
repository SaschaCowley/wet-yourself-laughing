"""Network component of the game."""

import socket
import selectors
from functools import partial
from queue import SimpleQueue, Empty
from .types import Payload
from .enums import CommandEnum, DirectionEnum, EventEnum, ErrorEnum
import multiprocessing as mp

logger = mp.get_logger()


def network_loop(queue: SimpleQueue[Payload],
                 local_ip: str,
                 local_port: int,
                 remote_ip: str,
                 remote_port: int) -> None:
    """Run the network communication loop."""
    logger.info("Local: %s:%d, Remote: %s:%d",
                local_ip, local_port, remote_ip, remote_port)
    try:
        sel = selectors.DefaultSelector()
        send_sock = socket.socket(family=socket.AF_INET,
                                  type=socket.SOCK_DGRAM)
        recv_sock = socket.socket(family=socket.AF_INET,
                                  type=socket.SOCK_DGRAM)
        recv_sock.bind((local_ip, local_port))
        send_sock.setblocking(False)
        recv_sock.setblocking(False)
        recv = partial(handle_udp_recv, queue)
        sel.register(recv_sock, selectors.EVENT_READ, recv)
    except OSError:
        queue.put(Payload(ErrorEnum.NETWORK_ERROR))
        exit()
    send = partial(handle_udp_send,
                   sock=send_sock,
                   ip=remote_ip,
                   port=remote_port)

    while True:
        try:
            payload, direction = queue.get(block=False)
            if direction == DirectionEnum.RECV:
                queue.put(Payload(payload=payload, others=direction))
                pass
            if direction == DirectionEnum.SEND:
                send(payload)
            if payload == CommandEnum.TERMINATE:
                break
        except Empty:
            pass

        events = sel.select(0)
        for key, mask in events:
            print("Got something...")
            callback = key.data
            callback(key.fileobj, mask)

    send_sock.close()
    recv_sock.close()
    sel.close()


def handle_udp_recv(queue: SimpleQueue[Payload],
                    sock: socket.socket,
                    mask: int) -> None:
    """Handle receiving a datagram."""
    data, addr = sock.recvfrom(1024)
    logger.debug("Received %s from %s:%d", data, *addr)
    try:
        payload = EventEnum(data)
        queue.put(Payload(payload, DirectionEnum.RECV))
    except ValueError:
        logger.exception("Dropping packet '%s'.", data)
        pass


def handle_udp_send(data: bytes,
                    sock: socket.socket,
                    ip: str,
                    port: int) -> int:
    """Handle sending a datagram.

    This is mainly here so we can make a partial of it.
    """
    print(f'Sending {data!r} to {ip}:{port}')
    return sock.sendto(data, (ip, port))
