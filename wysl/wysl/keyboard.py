"""Keyboard input part of the game."""

from queue import SimpleQueue
from .types import Payload
from .enums import CommandEnum


def keyboard_loop(queue: SimpleQueue[Payload]) -> None:
    """Keyboard input listener loop."""
    while True:
        received = input("> ").strip().casefold()
        if received == "quit":
            queue.put(Payload(CommandEnum.TERMINATE))
        else:
            print("I beg your pardon?")
