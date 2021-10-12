"""Type annotations."""

from __future__ import annotations

from typing import TypedDict, NamedTuple, Union, Any
from .enums import CommandEnum, DirectionEnum, EventEnum, ErrorEnum


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


class NetworkPayload(Payload):
    """Payload type for the network ITC queue."""

    payload: Union[EventEnum, CommandEnum]
    other: DirectionEnum


NonNetworkEnum = Union[CommandEnum, EventEnum, ErrorEnum]
