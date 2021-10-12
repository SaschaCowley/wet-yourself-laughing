"""Keyboard input part of the game."""

from queue import Queue
from .types import Payload
from .enums import CommandEnum


def keyboard_loop(queue: Queue[Payload]) -> None:
    """Keyboard input listener loop."""
    while True:
        received = input("> ").strip().casefold()
        if received == "quit":
            queue.put_nowait(Payload(CommandEnum.TERMINATE))
        else:
            print("I beg your pardon?")
