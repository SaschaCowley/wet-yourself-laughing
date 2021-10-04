"""Laughter detection component of the game."""

import time


def laughter_loop(pipe):
    """Laughter detection loop."""
    time.sleep(5)
    pipe.send("Hello from the laughter loop!")
