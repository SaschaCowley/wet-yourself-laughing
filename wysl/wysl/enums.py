"""Enumerations."""

from enum import Enum, auto


class StatusEnum(Enum):
    """Enumeration of statuses."""

    CAMERA_ERROR = auto()
    LAUGHTER_DETECTED = auto()


class CommandEnum(Enum):
    """Enumeration of statuses."""

    TERMINATE = auto()
