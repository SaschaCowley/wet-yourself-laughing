"""Keyboard input part of the game."""

from .enums import CommandEnum
from .types import ITCQueue, Payload


def keyboard_loop(queue: ITCQueue) -> None:
    """Keyboard input listener loop."""
    while True:
        received = input("> ").strip().casefold()
        if received == "quit":
            queue.put_nowait(Payload(CommandEnum.TERMINATE))
        elif received == "start":
            queue.put(Payload(CommandEnum.START))
        else:
            print("I beg your pardon?")
