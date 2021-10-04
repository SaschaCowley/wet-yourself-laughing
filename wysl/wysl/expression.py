"""Expression detection game component."""

import time


def expression_loop(pipe):
    """Expression detection loop."""
    time.sleep(10)
    pipe.send("Hello from the expression loop!")
