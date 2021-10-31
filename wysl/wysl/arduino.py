"""Arduino communication game component.

Communication with the arduino is handled by `arduino_loop`, which should be
run as a thread.
"""
import multiprocessing as mp
from queue import Empty

import serial

from .enums import CommandEnum, ErrorEnum
from .types import ITCQueue, Payload

logger = mp.get_logger()


def arduino_loop(queue: ITCQueue,
                 port: str,
                 baudrate: int = 9600) -> None:
    """Handle communication with the Arduino.

    Args:
        queue (ITCQueue): Queue object to use for inter-thread communication.
        port (str): Identifier of the port to which the Arduino is connected.
        baudrate (int, optional): Baudrate of the connection to establish.
            Defaults to 9600.
    """
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

    # Disable pulsing of relays and turn all relays off.
    ser.write(b'!A0!B0!C0!D0-A-B-C-D')
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

    # Cleanup
    # Disable pulsing of relays and turn all relays off.
    ser.write(b'!A0!B0!C0!D0-A-B-C-D')
    ser.close()
