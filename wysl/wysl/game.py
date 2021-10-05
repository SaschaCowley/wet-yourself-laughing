"""Game main process code."""

import logging
import multiprocessing as mp
import threading
from queue import SimpleQueue

from .enums import CommandEnum, StatusEnum
from .expression import expression_loop
from .laughter import laughter_loop

logger = mp.log_to_stderr()
logger.setLevel(1)
input_queue: SimpleQueue[str] = SimpleQueue()


def game_loop() -> None:
    """Main game loop."""
    global input_queue
    kb_thread = threading.Thread(
        target=keyboard_loop, name="KeyboardThread", daemon=True)
    kb_thread.start()
    expression_pipe_local, expression_pipe_remote = mp.Pipe()
    laughter_pipe_local, laughter_pipe_remote = mp.Pipe()
    expression_proc = mp.Process(
        name="ExpressionProcess",
        target=expression_loop,
        kwargs={"pipe": expression_pipe_remote, "camera_index": 1})
    laughter_proc = mp.Process(
        name="LaughterProcess",
        target=laughter_loop,
        kwargs={"pipe": laughter_pipe_remote})
    local_pipes: list[mp.connection.Connection] = [
        expression_pipe_local, laughter_pipe_local]
    # processes: list[mp.Process] = [expression_proc, laughter_proc]
    expression_proc.start()
    expression_proc.join(0)
    laughter_proc.start()
    laughter_proc.join(0)
    print("Hello from main game loop!")
    while True:
        ready = mp.connection.wait(local_pipes, 0)
        for pipe in ready:
            #if not isinstance(pipe, mp.connection.Connection):
                #continue
            payload = pipe.recv()
            logger.info(f'Received from {pipe}: {payload}')
            if payload is StatusEnum.CAMERA_ERROR:
                logger.error("Problem with the camera.")
            # print(payload)

        if not input_queue.empty():
            payload = input_queue.get()
            logger.info(f'Received input: {payload}')
            if payload == 'quit':
                expression_pipe_local.send(CommandEnum.TERMINATE)
        if not (expression_proc.is_alive() or laughter_proc.is_alive()):
            break


def keyboard_loop() -> None:
    """Keyboard input listener loop."""
    global input_queue
    while True:
        received = input("> ").strip().casefold()
        input_queue.put(received)
