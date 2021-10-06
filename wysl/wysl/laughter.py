"""Laughter detection component of the game."""

import multiprocessing as mp
import time


def laughter_loop(pipe: mp.connection.Connection) -> None:
    """Laughter detection loop."""
    time.sleep(5)
    pipe.send("Hello from the laughter loop!")
