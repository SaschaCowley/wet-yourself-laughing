"""Game main process code."""

# import logging
import multiprocessing as mp
import threading
from multiprocessing.connection import Connection, PipeConnection
from queue import Empty, SimpleQueue
from typing import Iterable, Union

from .arduino import arduino_loop
from .enums import CommandEnum, StatusEnum
from .exceptions import (CameraError, MicrophoneError, SerialError,
                         UserTerminationException)
from .expression import expression_loop
from .laughter import laughter_loop


logger = mp.log_to_stderr()
logger.setLevel(1)
input_queue: SimpleQueue[str] = SimpleQueue()
local_pipes: list[Connection]


def game_loop() -> None:
    """Run the primary game loop."""
    global input_queue, local_pipes
    kb_thread = threading.Thread(
        target=keyboard_loop, name="KeyboardThread", daemon=True)
    arduino_queue: SimpleQueue[Union[StatusEnum, CommandEnum]] = SimpleQueue()
    arduino_thread = threading.Thread(
        target=arduino_loop,
        name="ArduinoThread",
        kwargs={"queue": arduino_queue, "port": "COM6"})
    expression_pipe_local, expression_pipe_remote = mp.Pipe()
    laughter_pipe_local, laughter_pipe_remote = mp.Pipe()
    local_pipes = [expression_pipe_local, laughter_pipe_local]
    queues = [arduino_queue]
    expression_proc = mp.Process(
        name="ExpressionProcess",
        target=expression_loop,
        kwargs={"pipe": expression_pipe_remote, "camera_index": 1})
    laughter_proc = mp.Process(
        name="LaughterProcess",
        target=laughter_loop,
        kwargs={"pipe": laughter_pipe_remote})
    # processes: list[mp.Process] = [expression_proc, laughter_proc]
    expression_proc.start()
    expression_proc.join(0)
    laughter_proc.start()
    laughter_proc.join(0)
    kb_thread.start()
    arduino_thread.start()
    print("Hello from main game loop!")
    while True:
        try:
            handle_ipc_recv()
            handle_itc_recv(queues)
            handle_keyboard_input()

        except CameraError:
            logger.info("Shutting down due to camera error.")
            break
        except MicrophoneError:
            logger.info("Shutting down due to microphone error.")
            break
        except SerialError:
            logger.info("Shutting down due to serial error.")
            break
        except UserTerminationException:
            logger.info("Shutting down at user request.")
            break

        if not (expression_proc.is_alive() or laughter_proc.is_alive()):
            break

    shutdown(queues)


def handle_ipc_recv() -> None:
    """Handle inter-process communication in the receive direction."""
    ready = mp.connection.wait(local_pipes, 0)
    for pipe in ready:
        if not isinstance(pipe, (Connection, PipeConnection)):
            continue
        payload = pipe.recv()
        logger.info(f'Received from {pipe}: {payload}')
        if payload is StatusEnum.CAMERA_ERROR:
            logger.error("Problem with the camera.")
            raise CameraError
        elif payload is StatusEnum.MICROPHONE_ERROR:
            logger.error("Problem with the microphone.")
            raise MicrophoneError
        elif payload is CommandEnum.TERMINATE:
            raise UserTerminationException


def handle_itc_recv(
        queues: Iterable[SimpleQueue[Union[StatusEnum, CommandEnum]]]) -> None:
    """Handle inter-thread communication in the receive direction."""
    for queue in queues:
        try:
            payload = queue.get(block=False)
            if payload is StatusEnum.SERIAL_ERROR:
                logger.error("Problem with the serial device.")
                raise SerialError
            else:
                queue.put(payload)
        except Empty:
            continue


def handle_keyboard_input() -> None:
    """Handle user keyboard input."""
    if not input_queue.empty():
        payload = input_queue.get()
        logger.info(f'Received input: {payload}')
        if payload == 'quit':
            raise UserTerminationException


def shutdown(queues: Iterable[SimpleQueue[Union[StatusEnum, CommandEnum]]]) -> None:
    """Shutdown the game."""
    global local_pipes
    for pipe in local_pipes:
        try:
            pipe.send(CommandEnum.TERMINATE)
        except (OSError, BrokenPipeError):
            continue
    for queue in queues:
        queue.put(CommandEnum.TERMINATE)


def keyboard_loop() -> None:
    """Keyboard input listener loop."""
    global input_queue
    while True:
        received = input("> ").strip().casefold()
        input_queue.put(received)
