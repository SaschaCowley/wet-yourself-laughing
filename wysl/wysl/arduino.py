"""Arduino communication game component."""

import serial
import multiprocessing as mp
from .enums import CommandEnum, ErrorEnum
from .types import Payload

from queue import SimpleQueue, Empty

logger = mp.get_logger()


def arduino_loop(queue: SimpleQueue[Payload],
                 port: str,
                 baudrate: int = 9600) -> None:
    """Arduino communication loop."""
    logger.info("Port: %s, baudrate: %d", port, baudrate)
    channels = [False, False]
    try:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=0)
    except (ValueError, serial.SerialException) as e:
        logger.error(e)
        queue.put(Payload(ErrorEnum.SERIAL_ERROR))
        exit()
    ser.write(b'abcd')
    while True:
        try:
            payload, other = queue.get(block=False)
            if payload == CommandEnum.TERMINATE:
                break
            elif payload == CommandEnum.CHANNEL_1_ON and channels[0] is False:
                ser.write(b'A')
                channels[0] = True
            elif payload == CommandEnum.CHANNEL_1_OFF and channels[0] is True:
                ser.write(b'a')
                channels[0] = False
            elif payload == CommandEnum.CHANNEL_2_ON and channels[1] is False:
                ser.write(b'B')
                channels[1] = True
            elif payload == CommandEnum.CHANNEL_2_OFF and channels[1] is True:
                ser.write(b'b')
                channels[1] = False
            else:
                queue.put(Payload(payload, other))
        except Empty:
            continue

    ser.write(b'abcd')
    ser.close()
