"""Enumerations."""

from enum import Enum, auto


class ErrorEnum(Enum):
    """Enumeration of errors."""

    CAMERA_ERROR = auto()
    MICROPHONE_ERROR = auto()
    SERIAL_ERROR = auto()
    NETWORK_ERROR = auto()


class EventEnum(Enum):
    """Enumeration of statuses."""

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
    """Enumeration of statuses."""

    TERMINATE = auto()
    CHANNEL_ON = '+'
    CHANNEL_OFF = '-'
    PULSE_CHANNEL = '!'
    QUERY_CHANNEL = '?'


class ChannelEnum(Enum):
    """Enumeration of relay channels."""

    CHANNEL_1 = 'A'
    CHANNEL_2 = 'B'
    CHANNEL_3 = 'C'
    CHANNEL_4 = 'D'


class DirectionEnum(Enum):
    """Enumeration of statuses."""

    SEND = auto()
    RECV = auto()


class LocationEnum(Enum):
    """Enumeration of locations."""

    LOCAL = auto()
    REMOTE = auto()
