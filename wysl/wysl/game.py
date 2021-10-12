"""Game main process code."""


from configparser import ConfigParser
import multiprocessing as mp
import threading
from multiprocessing.connection import Connection, PipeConnection
from queue import Empty, SimpleQueue
from typing import Mapping, Protocol
from functools import partial
from .arduino import arduino_loop
from .enums import CommandEnum, EventEnum, ErrorEnum, ChannelEnum
from .exceptions import (CameraError, MicrophoneError, SerialError,
                         NetworkError, UserTerminationException)
from .expression import expression_loop
from .laughter import laughter_loop
from .network import network_loop
from .types import Payload

Queues = Mapping[str, SimpleQueue[Payload]]
Pipes = Mapping[str, Connection]


class PartialSetChannel(Protocol):
    """Type hint for set_arduino_channel."""

    def __call__(_, channel: int,
                 state: CommandEnum,
                 interval: int = 0) -> None:
        """Call, dummy."""
        ...


logger = mp.log_to_stderr()
logger.setLevel(1)

set_arduino_channel: PartialSetChannel


def game_loop(config: ConfigParser) -> None:
    """Run the primary game loop."""
    global set_arduino_channel, pulse_interval, pulse
    # Configuration sections for easier access
    arduino_cfg = config["arduino"]
    expression_cfg = config['expression']
    laughter_cfg = config["laughter"]
    network_cfg = config['network']

    # IPC and ITC communication constructs
    # Create ITC queues
    input_queue: SimpleQueue[str] = SimpleQueue()
    arduino_queue: SimpleQueue[Payload] = SimpleQueue()
    network_queue: SimpleQueue[Payload] = SimpleQueue()
    queues: Queues = {
        "ArduinoQueue": arduino_queue,
        "NetworkQueue": network_queue,
    }

    # Create IPC pipes
    expression_pipe_local, expression_pipe_remote = mp.Pipe()
    laughter_pipe_local, laughter_pipe_remote = mp.Pipe()
    local_pipes = {
        "ExpressionPipe": expression_pipe_local,
        "LaughterPipe": laughter_pipe_local
    }

    # Create threads
    kb_thread = threading.Thread(
        target=keyboard_loop,
        name="KeyboardThread",
        daemon=True,
        kwargs={
            "queue": input_queue
        })

    arduino_thread = threading.Thread(
        target=arduino_loop,
        name="ArduinoThread",
        kwargs={
            "queue": arduino_queue,
            "port": arduino_cfg.get("port"),
            "baudrate": arduino_cfg.getint("baudrate")
        })

    network_thread = threading.Thread(
        target=network_loop,
        name="NetworkThread",
        kwargs={
            "queue": network_queue,
            "local_ip": network_cfg.get("local_ip"),
            "local_port": network_cfg.getint("local_port"),
            "remote_ip": network_cfg.get("remote_ip"),
            "remote_port": network_cfg.getint("remote_port")
        })

    # Create processes
    expression_proc = mp.Process(
        name="ExpressionProcess",
        target=expression_loop,
        kwargs={
            "pipe": expression_pipe_remote,
            "mtcnn": expression_cfg.getboolean("mtcnn"),
            "camera_index": expression_cfg.getint("camera_index"),
            "happy_weight": expression_cfg.getfloat("happy_weight"),
            "surprise_weight": expression_cfg.getfloat("surprise_weight"),
            "low_threshhold": expression_cfg.getfloat("low_threshhold"),
            "medium_threshhold": expression_cfg.getfloat("medium_threshhold"),
            "high_threshhold": expression_cfg.getfloat("high_threshhold")
        })

    laughter_proc = mp.Process(
        name="LaughterProcess",
        target=laughter_loop,
        kwargs={
            "pipe": laughter_pipe_remote,
            "microphone_index": laughter_cfg.getint("microphone_index"),
            "rate": laughter_cfg.getint("rate"),
            "channels": laughter_cfg.getint("channels"),
            "width": laughter_cfg.getint("width"),
            "chunk_duration": laughter_cfg.getfloat("chunk_duration"),
            "mean": laughter_cfg.getfloat("mean"),
            "stddev": laughter_cfg.getfloat("stddev"),
            "records": laughter_cfg.getint("records"),
            "hits": laughter_cfg.getint("hits")
        })

    # Partials for convenience
    set_arduino_channel = partial(switch_channel, arduino_queue)

    # Start and join all threads and processes
    # expression_proc.start()
    # expression_proc.join(0)
    # laughter_proc.start()
    # laughter_proc.join(0)
    kb_thread.start()
    kb_thread.join(0)
    arduino_thread.start()
    arduino_thread.join(0)
    network_thread.start()
    network_thread.join(0)

    # Main event loop
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
        except NetworkError:
            logger.info("Shutting down due to network error.")
            break
        except UserTerminationException:
            logger.info("Shutting down at user request.")
            break

        # if not (expression_proc.is_alive() or laughter_proc.is_alive()):
            # break

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
        if payload is ErrorEnum.CAMERA_ERROR:
            logger.error("Problem with the camera.")
            raise CameraError
        elif payload is ErrorEnum.MICROPHONE_ERROR:
            logger.error("Problem with the microphone.")
            raise MicrophoneError
        elif payload is CommandEnum.TERMINATE:
            raise UserTerminationException
        elif payload is EventEnum.LAUGHTER_DETECTED:
            set_arduino_channel(channel=1, state=CommandEnum.CHANNEL_ON)
        elif payload is EventEnum.NO_LAUGHTER_DETECTED:
            set_arduino_channel(channel=1, state=CommandEnum.CHANNEL_OFF)


def handle_itc_recv(queues: Queues) -> None:
    """Handle inter-thread communication in the receive direction."""
    for name, queue in queues.items():
        try:
            payload, other = queue.get(block=False)
            if payload is ErrorEnum.SERIAL_ERROR:
                logger.error("Problem with the serial device.")
                raise SerialError
            elif payload is ErrorEnum.NETWORK_ERROR:
                logger.error("Problem with the network socket device.")
                raise NetworkError
            else:
                queue.put(Payload(payload, other))
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
    global set_arduino_channel
    for i in range(1, 5):
        set_arduino_channel(i, CommandEnum.PULSE_CHANNEL, 0)
        set_arduino_channel(i, CommandEnum.CHANNEL_OFF)
    for name, pipe in pipes.items():
        try:
            pipe.send(CommandEnum.TERMINATE)
        except (OSError, BrokenPipeError):
            continue
    for name, queue in queues.items():
        queue.put(Payload(CommandEnum.TERMINATE))


def keyboard_loop(queue: SimpleQueue[str]) -> None:
    """Keyboard input listener loop."""
    while True:
        received = input("> ").strip().casefold()
        queue.put(received)


def switch_channel(queue: SimpleQueue[Payload],
                   channel: int,
                   state: CommandEnum,
                   interval: int = 0) -> None:
    """Set the arduino channel."""
    if channel == 1:
        ch = ChannelEnum.CHANNEL_1
    elif channel == 2:
        ch = ChannelEnum.CHANNEL_2
    elif channel == 3:
        ch = ChannelEnum.CHANNEL_3
    elif channel == 4:
        ch = ChannelEnum.CHANNEL_4
    else:
        return
    if state == CommandEnum.CHANNEL_ON or state == CommandEnum.CHANNEL_OFF:
        queue.put(Payload(state, ch))
    elif state == CommandEnum.PULSE_CHANNEL:
        queue.put(Payload(state, (ch, interval)))
    else:
        return
