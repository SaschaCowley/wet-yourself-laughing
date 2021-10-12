"""Arduino communication game component."""
import serial
import multiprocessing as mp
from .enums import CommandEnum, ErrorEnum
from .types import Payload, ITCQueue

from queue import Empty

logger = mp.get_logger()


def arduino_loop(queue: ITCQueue,
                 port: str,
                 baudrate: int = 9600) -> None:
    """Arduino communication loop."""
    logger.info("Port: %s, baudrate: %d", port, baudrate)
    try:
        # dsrdtr=True seems to fix the problem where reads within 1-2 seconds
        # of opening the port fail silently. See
        # https://github.com/pyserial/pyserial/issues/329#issuecomment-791997557
        ser = serial.Serial(port=port,
                            baudrate=baudrate,
                            timeout=0,
                            dsrdtr=True)
    except (ValueError, serial.SerialException) as e:
        logger.error(e)
        queue.put_nowait(Payload(ErrorEnum.SERIAL_ERROR))
        exit()
    ser.write(b'abcd')
    while True:
        try:
            payload, other = queue.get(block=False)
            msg = ''
            if payload == CommandEnum.TERMINATE:
                break
            elif (payload == CommandEnum.CHANNEL_ON
                    or payload == CommandEnum.CHANNEL_OFF):
                msg += payload.value + other.value
            elif payload == CommandEnum.PULSE_CHANNEL:
                msg += payload.value + other[0].value + str(other[1])
            else:
                pass
            ser.write(bytes(msg, encoding='ascii'))
        except Empty:
            continue

    ser.close()
