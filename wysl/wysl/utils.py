"""Utility functions."""

from typing import NamedTuple, Iterable, Any
from multiprocessing.connection import Connection


class ExpressionPayload(NamedTuple):
    """Expression information payload."""

    happy: float
    surprise: float

    @classmethod
    def from_fer_dict(cls, fer_dict):
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
