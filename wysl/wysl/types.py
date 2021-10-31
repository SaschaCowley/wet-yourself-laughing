"""Type annotations.

These should just be type annotations for use throughout the code base.
"""

from __future__ import annotations

from collections import deque
from multiprocessing.connection import Connection
from queue import Queue
from typing import (Any, Callable, Mapping, NamedTuple, Protocol, TypedDict,
                    Union)

from .enums import CommandEnum, ErrorEnum, EventEnum, LocationEnum


class FERDict(TypedDict):
    """Type annotation for box+emotion dictionaries returned by FER."""

    box: list[int]
    emotions: FEREmotions


class FEREmotions(TypedDict):
    """Type annotation for emotion dictionaries returned by FER."""

    angry: float
    disgust: float
    fear: float
    happy: float
    neutral: float
    sad: float
    surprise: float


class Payload(NamedTuple):
    """Payload type for ITC queues."""

    payload: NonNetworkEnum
    others: Any = None


class EventHandler(Protocol):
    """Type hint for event_handler."""

    def __call__(_, *,
                 event: EventEnum,
                 location: LocationEnum) -> None:
        """Call, dummy."""
        ...


class ChannelSetter(Protocol):
    """Type hint for set_arduino_channel."""

    def __call__(_, channel: int,
                 state: CommandEnum,
                 interval: int = 0) -> None:
        """Call, dummy."""
        ...


ITCQueue = Queue[Payload]
Queues = Mapping[str, ITCQueue]
Pipes = Mapping[str, Connection]
NonNetworkEnum = Union[CommandEnum, EventEnum, ErrorEnum]
ExpressionClassifier = Callable[[FEREmotions], EventEnum]
FERList = list[FERDict]
FloatDeque = deque[float]
