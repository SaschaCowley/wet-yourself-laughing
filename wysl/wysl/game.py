"""Game main process code."""

# import logging
import multiprocessing as mp
import threading
from multiprocessing.connection import Connection, PipeConnection
from queue import Empty, SimpleQueue
from typing import Mapping, Union, Protocol
from functools import partial

from .arduino import arduino_loop
from .enums import CommandEnum, StatusEnum
from .exceptions import (CameraError, MicrophoneError, SerialError,
                         UserTerminationException)
from .expression import expression_loop
from .laughter import laughter_loop

Queues = Mapping[str, SimpleQueue[Union[CommandEnum, StatusEnum]]]
Pipes = Mapping[str, Connection]


class PartialSetChannel(Protocol):
    """Type hint for set_arduino_channel."""

    def __call__(_, channel: int, state: bool) -> None:
        """Call, dummy."""
        ...


logger = mp.log_to_stderr()
logger.setLevel(1)
set_arduino_channel: PartialSetChannel


def game_loop() -> None:
    """Run the primary game loop."""
    global set_arduino_channel
    input_queue: SimpleQueue[str] = SimpleQueue()
    kb_thread = threading.Thread(
        target=keyboard_loop,
        name="KeyboardThread",
        daemon=True,
        kwargs={"queue": input_queue})
    arduino_queue: SimpleQueue[Union[StatusEnum, CommandEnum]] = SimpleQueue()
    set_arduino_channel = partial(switch_channel, queue=arduino_queue)
    arduino_thread = threading.Thread(
        target=arduino_loop,
        name="ArduinoThread",
        kwargs={"queue": arduino_queue, "port": "COM6"}, daemon=True)
    expression_pipe_local, expression_pipe_remote = mp.Pipe()
    laughter_pipe_local, laughter_pipe_remote = mp.Pipe()
    local_pipes = {
        "ExpressionPipe": expression_pipe_local,
        "LaughterPipe": laughter_pipe_local}
    queues: Queues = {"ArduinoQueue": arduino_queue}
    expression_proc = mp.Process(
        name="ExpressionProcess",
        target=expression_loop,
        kwargs={"pipe": expression_pipe_remote, "camera_index": 1})
    laughter_proc = mp.Process(
        name="LaughterProcess",
        target=laughter_loop,
        kwargs={"pipe": laughter_pipe_remote})
    # processes: list[mp.Process] = [expression_proc, laughter_proc]
    # expression_proc.start()
    # expression_proc.join(0)
    laughter_proc.start()
    laughter_proc.join(0)
    kb_thread.start()
    arduino_thread.start()
    while True:
        try:
            handle_ipc_recv(local_pipes)
            handle_itc_recv(queues)
            handle_keyboard_input(input_queue)

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

    shutdown(local_pipes, queues)


def handle_ipc_recv(pipes: Pipes) -> None:
    """Handle inter-process communication in the receive direction."""
    global set_arduino_channel
    ready = mp.connection.wait(pipes.values(), 0)
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
        elif payload is StatusEnum.LAUGHTER_DETECTED:
            set_arduino_channel(channel=1, state=True)
        elif payload is StatusEnum.NO_LAUGHTER_DETECTED:
            set_arduino_channel(channel=1, state=False)


def handle_itc_recv(queues: Queues) -> None:
    """Handle inter-thread communication in the receive direction."""
    for name, queue in queues.items():
        try:
            payload = queue.get(block=False)
            if payload is StatusEnum.SERIAL_ERROR:
                logger.error("Problem with the serial device.")
                raise SerialError
            else:
                queue.put(payload)
        except Empty:
            continue


def handle_keyboard_input(input_queue: SimpleQueue[str]) -> None:
    """Handle user keyboard input."""
    if not input_queue.empty():
        payload = input_queue.get()
        logger.info(f'Received input: {payload}')
        if payload == 'quit':
            raise UserTerminationException


def shutdown(pipes: Pipes, queues: Queues) -> None:
    """Shutdown the game."""
    for name, pipe in pipes.items():
        try:
            pipe.send(CommandEnum.TERMINATE)
        except (OSError, BrokenPipeError):
            continue
    for name, queue in queues.items():
        queue.put(CommandEnum.TERMINATE)


def keyboard_loop(queue: SimpleQueue[str]) -> None:
    """Keyboard input listener loop."""
    while True:
        received = input("> ").strip().casefold()
        queue.put(received)


def switch_channel(queue: SimpleQueue[Union[StatusEnum, CommandEnum]],
                   channel: int,
                   state: bool) -> None:
    """Set the arduino channel."""
    if channel == 1 and state is True:
        queue.put(CommandEnum.CHANNEL_1_ON, block=False)
    elif channel == 1 and state is False:
        queue.put(CommandEnum.CHANNEL_1_OFF, block=False)
    elif channel == 2 and state is True:
        queue.put(CommandEnum.CHANNEL_2_ON, block=False)
    elif channel == 2 and state is False:
        queue.put(CommandEnum.CHANNEL_2_OFF, block=False)
    else:
        raise ValueError(
            f'Unknown combination of channel and state: {channel}, {state}.')
