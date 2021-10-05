"""Utility functions."""

from typing import NamedTuple


class ExpressionPayload(NamedTuple):
    """Expression information payload."""

    happy: float
    surprise: float


def elicit_int(prompt="",
               values=None,
               err="Invalid input, try again",
               default=None):
    """Prompt the user for an integer."""
    i = None
    while i is None:
        try:
            i = input(prompt).strip()
            if i == "" and default is not None:
                i = default
            else:
                i = int(i)
            if i is not None and i not in values:
                raise ValueError
        except ValueError:
            print(err)
            i = None
    return i
