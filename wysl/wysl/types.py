"""Type annotations."""

from __future__ import annotations

from typing import TypedDict


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
