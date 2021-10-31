"""Enumerations.

Some of these have auto() values, but some of them have specific bytes values
so they can be used as UDP commands.
"""

from enum import Enum, auto


class ErrorEnum(Enum):
    """Enumeration of errors."""

    CAMERA_ERROR = auto()
    MICROPHONE_ERROR = auto()
    SERIAL_ERROR = auto()
    NETWORK_ERROR = auto()


class EventEnum(Enum):
    """Enumeration of game events.

    These values are given as bytes so they can easily be used as the contents
    of UDP packets.
    """

    NO_LAUGHTER_DETECTED = b'No laughter detected'
    LAUGHTER_DETECTED = b'Laughter detected'
    NO_SMILE_DETECTED = b'No smile detected'
    LOW_INTENSITY_SMILE_DETECTED = b'Low intensity smile detected'
    MEDIUM_INTENSITY_SMILE_DETECTED = b'Medium intensity smile detected'
    HIGH_INTENSITY_SMILE_DETECTED = b'High intensity smile detected'
    GAME_OVER = b'Game over'
    START_GAME = b'Start game'
    END_GAME = b'End game'
    HANDSHAKE = b'Handshake'
    HANDSHAKE_RECEIVED = b'Hello'


class CommandEnum(Enum):
    """Enumeration of inter-thread/process communication commands.

    The values CHANNEL_ON, CHANNEL_OFF, PULSE_CHANNEL and QUERY_CHANNEL are
    given as bytes so that Arduino controller commands can be easily composed
    from their values.
    """

    TERMINATE = auto()
    START = auto()
    CHANNEL_ON = '+'
    CHANNEL_OFF = '-'
    PULSE_CHANNEL = '!'
    QUERY_CHANNEL = '?'


class ChannelEnum(Enum):
    """Enumeration of relay channels.

    These values are given as bytes so that Arduino controller commands can be
    easily composed from their values.
    """

    CHANNEL_1 = 'A'
    CHANNEL_2 = 'B'
    CHANNEL_3 = 'C'
    CHANNEL_4 = 'D'


class DirectionEnum(Enum):
    """Enumeration of directions for UDP communications."""

    SEND = auto()
    RECV = auto()


class LocationEnum(Enum):
    """Enumeration of origins for game events."""

    LOCAL = auto()
    REMOTE = auto()
