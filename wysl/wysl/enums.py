"""Enumerations."""

from enum import Enum, auto


class StatusEnum(Enum):
    """Enumeration of statuses."""

    CAMERA_ERROR = auto()
    MICROPHONE_ERROR = auto()
    NO_LAUGHTER_DETECTED = auto()
    LAUGHTER_DETECTED = auto()
    NO_SMILE_DETECTED = auto()
    LOW_INTENSITY_SMILE_DETECTED = auto()
    MEDIUM_INTENSITY_SMILE_DETECTED = auto()
    HIGH_INTENSITY_SMILE_DETECTED = auto()


class CommandEnum(Enum):
    """Enumeration of statuses."""

    TERMINATE = auto()
