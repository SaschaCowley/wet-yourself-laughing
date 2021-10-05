"""Game main process code."""

import multiprocessing as mp
import threading
import logging
from .laughter import laughter_loop
from .expression import expression_loop
from .enums import StatusEnum, CommandEnum
from queue import SimpleQueue

logger = mp.log_to_stderr()
logger.setLevel(logging.INFO)

input_queue: SimpleQueue[str] = SimpleQueue()


def game_loop():
    """Main game loop."""
    global input_queue
    kb_thread = threading.Thread(target=keyboard_loop, name="KeyboardThread", daemon=True)
    kb_thread.start()
    expression_pipe_recv, expression_pipe_send = mp.Pipe()
    laughter_pipe_recv, laughter_pipe_send = mp.Pipe()
    expression_proc = mp.Process(
        name="ExpressionProcess",
        target=expression_loop,
        kwargs={"pipe": expression_pipe_send, "camera_index": 1})
    laughter_proc = mp.Process(
        name="LaughterProcess",
        target=laughter_loop,
        kwargs={"pipe": laughter_pipe_send})
    expression_proc.start()
    expression_proc.join(0)
    laughter_proc.start()
    laughter_proc.join(0)
    print("Hello from main game loop!")
    while True:
        ready = mp.connection.wait(
            [expression_pipe_recv, laughter_pipe_recv], 0)
        for pipe in ready:
            payload = pipe.recv()
            logger.debug(f'Received from {pipe}: {payload}')
            print(payload)

        if not input_queue.empty():
            payload = input_queue.get()
            print(f'Latest input received: {payload}')
            if payload == 'quit':
                expression_pipe_recv.send(CommandEnum.TERMINATE)
        if not (expression_proc.is_alive() or laughter_proc.is_alive()):
            break


def keyboard_loop():
    """Keyboard input listener loop."""
    global input_queue
    while True:
        received = input("> ")
        input_queue.put(received)
