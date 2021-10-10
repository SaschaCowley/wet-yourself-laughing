"""Arduino communication game component."""

from typing import Union
import serial
import multiprocessing as mp
from .enums import StatusEnum, CommandEnum

from queue import SimpleQueue, Empty

logger = mp.get_logger()


def arduino_loop(queue: SimpleQueue[Union[StatusEnum, CommandEnum]],
                 port: str,
                 baudrate: int = 9600) -> None:
    """Arduino communication loop."""
    try:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=0)
    except (ValueError, serial.SerialException) as e:
        logger.error(e)
        queue.put(StatusEnum.SERIAL_ERROR)
        exit()

    while True:
        try:
            payload = queue.get(block=False)
            if payload == CommandEnum.TERMINATE:
                break
            elif payload == CommandEnum.CHANNEL_1_ON:
                ser.send(b'A')
            elif payload == CommandEnum.CHANNEL_1_OFF:
                ser.send(b'a')
            elif payload == CommandEnum.CHANNEL_2_ON:
                ser.send(b'B')
            elif payload == CommandEnum.CHANNEL_2_OFF:
                ser.send(b'b')
            else:
                queue.put(payload)
        except Empty:
            continue

    ser.close()
