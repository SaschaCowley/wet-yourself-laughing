"""Network component of the game.

Note that, while this code includes some error checking, due to the nature of
UDP this is only local.
"""

import multiprocessing as mp
import selectors
import socket
from functools import partial
from queue import Empty

from .enums import CommandEnum, DirectionEnum, ErrorEnum, EventEnum
from .types import ITCQueue, Payload

logger = mp.get_logger()


def network_loop(queue: ITCQueue,
                 local_ip: str,
                 local_port: int,
                 remote_ip: str,
                 remote_port: int) -> None:
    """Run the network communication loop.

    Args:
        queue (ITCQueue): Queue object to be used for inter-thread
            communication.
        local_ip (str): IP v4 address of this machine (i.e., the receive
            address).
        local_port (int): Port on which to listen.
        remote_ip (str): IP v4 address of the remote machine (i.e., the send
            address).
        remote_port (int): Port on which to write.
    """
    logger.info("Local: %s:%d, Remote: %s:%d",
                local_ip, local_port, remote_ip, remote_port)

    # Setup our sending and receiving sockets.
    # While we are checking for errors, due to there being no ongoing
    # connection over UDP, the only errors we can detect here are connections
    # on the local side.
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
        queue.put_nowait(Payload(ErrorEnum.NETWORK_ERROR))
        exit()

    # For later convenience.
    send = partial(handle_udp_send,
                   sock=send_sock,
                   ip=remote_ip,
                   port=remote_port)

    while True:
        try:
            payload, direction = queue.get(block=False)
            # Put any received packets back on the queue for handling in the
            # parent thread.
            if direction == DirectionEnum.RECV:
                queue.put_nowait(Payload(payload=payload, others=direction))
            # Send any outstanding messages.
            if direction == DirectionEnum.SEND:
                send(payload.value)

            if payload == CommandEnum.TERMINATE:
                break
        except Empty:
            pass

        # Deal with any sockets that are able to be read.
        events = sel.select(0)  # Non-blocking
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)

    # Clean up after ourselves.
    send_sock.close()
    recv_sock.close()
    sel.close()


def handle_udp_recv(queue: ITCQueue,
                    sock: socket.socket,
                    mask: int) -> None:
    """Handle receiving a datagram.

    Args:
        queue (ITCQueue): Queue used for inter-tghread communication; the
            destination for received packets.
        sock (socket.socket): The socket we're receiving from.
        mask (int): The status mask.
    """
    data, addr = sock.recvfrom(1024)
    logger.debug("Received %s from %s:%d", data, *addr)
    try:
        payload = EventEnum(data)
        queue.put_nowait(Payload(payload, DirectionEnum.RECV))
    except ValueError:
        logger.exception("Dropping packet '%s'.", data)
        pass


def handle_udp_send(data: bytes,
                    sock: socket.socket,
                    ip: str,
                    port: int) -> int:
    """Handle sending a datagram.

    This mainly exists so we can make a partial of it.

    Args:
        data (bytes): Message payload to send.
        sock (socket.socket): Socket on which to send the message.
        ip (str): IP v4 address to which to send the message.
        port (int): Port number to which to send the message.

    Returns:
        int: [description]
    """
    no = sock.sendto(data, (ip, port))
    return no
