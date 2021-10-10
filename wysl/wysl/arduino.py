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
    channels = [False, False]
    try:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=0)
    except (ValueError, serial.SerialException) as e:
        logger.error(e)
        queue.put(StatusEnum.SERIAL_ERROR)
        exit()
    print("Hello from arduino thread!")
    while True:
        try:
            payload = queue.get(block=False)
            print(f"Arduino thread got {payload}")
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
                queue.put(payload)
        except Empty:
            continue

    ser.close()
