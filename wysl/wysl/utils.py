"""Utility functions."""

from __future__ import annotations

from typing import Iterable, Optional


def elicit_int(prompt: str = "",
               values: Optional[Iterable[int]] = None,
               err: str = "Invalid input, try again",
               default: Optional[int] = None) -> int:
    """Prompt the user for an integer."""
    while True:
        try:
            i = input(prompt).strip()
            if i == "" and default is not None:
                return default
            n = int(i)
            if values is not None and n not in values:
                raise ValueError
            return n
        except ValueError:
            print(err)
