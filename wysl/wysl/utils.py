"""Utility functions."""

from __future__ import annotations

from multiprocessing.connection import Connection
from typing import Any, Iterable, NamedTuple, Union
from .types import FERDict


class ExpressionPayload(NamedTuple):
    """Expression information payload."""

    happy: float
    surprise: float

    @classmethod
    def from_fer_dict(cls, fer_dict: FERDict) -> ExpressionPayload:
        """Create an ExpressionPayload object from an FER dictionary.

        Args:
            fer_dict (dict): Dict as returned by FER.

        Returns:
            ExpressionPayload: Equivalent expression payload object.
        """
        return cls(
            happy=fer_dict['emotions']['happy'],
            surprise=fer_dict['emotions']['surprise']
        )


NullableExpressionPayload = Union[ExpressionPayload, None]


def bcast(cons: Iterable[Connection], msg: Any) -> None:
    """Send a message to multiple pipes.

    Args:
        cons (Iterable[Connection]): The multiprocessing Connection objects to
            which to broadcast the message.
        msg (Any): The message to broadcast.

    Returns:
        None
    """
    for con in cons:
        con.send(msg)


def elicit_int(prompt: str = "",
               values: Union[Iterable[int], None] = None,
               err: str = "Invalid input, try again",
               default: Union[int, None] = None) -> int:
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
