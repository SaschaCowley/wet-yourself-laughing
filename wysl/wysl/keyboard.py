"""Keyboard input part of the game."""

from .enums import CommandEnum
from .types import ITCQueue, Payload


def keyboard_loop(queue: ITCQueue) -> None:
    """Keyboard input listener loop.

    Args:
        queue (ITCQueue): Queue object to be used for inter-thread
            communication.
    """
    while True:
        received = input("> ").strip().casefold()
        if received == "quit":
            queue.put_nowait(Payload(CommandEnum.TERMINATE))
            break
        elif received == "start":
            queue.put(Payload(CommandEnum.START))
        else:
            print("I beg your pardon?")
