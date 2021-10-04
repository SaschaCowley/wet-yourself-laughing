"""Game main process code."""

import multiprocessing as mp
from .laughter import laughter_loop
from .expression import expression_loop


def game_loop():
    """Main game loop."""
    expression_pipe_recv, expression_pipe_send = mp.Pipe()
    laughter_pipe_recv, laughter_pipe_send = mp.Pipe()
    expression_proc = mp.Process(
        target=expression_loop,
        kwargs={"pipe": expression_pipe_send, "camera_index": 1})
    laughter_proc = mp.Process(
        target=laughter_loop,
        kwargs={"pipe": laughter_pipe_send})
    expression_proc.start()
    expression_proc.join(0)
    laughter_proc.start()
    laughter_proc.join(0)
    print("Hello from main game loop!")
    while expression_proc.is_alive() and laughter_proc.is_alive():
        ready = mp.connection.wait(
            [expression_pipe_recv, laughter_pipe_recv], 0)
        for pipe in ready:
            print(pipe.recv())
