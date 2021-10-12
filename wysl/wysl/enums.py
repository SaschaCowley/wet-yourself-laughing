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


class CommandEnum(Enum):
    """Enumeration of statuses."""

    TERMINATE = auto()
    CHANNEL_1_ON = auto()
    CHANNEL_1_OFF = auto()
    CHANNEL_2_ON = auto()
    CHANNEL_2_OFF = auto()


class DirectionEnum(Enum):
    """Enumeration of statuses."""

    SEND = auto()
    RECV = auto()
