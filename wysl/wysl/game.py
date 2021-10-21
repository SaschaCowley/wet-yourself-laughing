"""Game main process code."""

import multiprocessing as mp
import threading
import time
from configparser import ConfigParser
from functools import partial
from multiprocessing.connection import Connection, PipeConnection
from queue import Empty, Queue

from .arduino import arduino_loop
from .enums import (ChannelEnum, CommandEnum, DirectionEnum, ErrorEnum,
                    EventEnum, LocationEnum)
from .exceptions import (CameraError, GameOverException, MicrophoneError,
                         NetworkError, SerialError, UserTerminationException)
from .expression import expression_loop
from .keyboard import keyboard_loop
from .laughter import laughter_loop
from .network import network_loop
from .types import (ChannelSetter, EventHandler, ITCQueue, Payload, Pipes,
                    Queues)
from .utils import box_strings

logger = mp.log_to_stderr()
# logger.setLevel(1)

set_arduino_channel: ChannelSetter
in_game = False


def game_loop(config: ConfigParser) -> None:
    """Run the primary game loop."""
    global set_arduino_channel, pulse_interval, pulse
    # Configuration sections for easier access
    arduino_cfg = config["arduino"]
    expression_cfg = config['expression']
    laughter_cfg = config["laughter"]
    network_cfg = config['network']
    game_cfg = config['game']

    # IPC and ITC communication constructs
    # Create ITC queues
    input_queue: ITCQueue = Queue()
    arduino_queue: ITCQueue = Queue()
    network_queue: ITCQueue = Queue()
    queues: Queues = {
        "ArduinoQueue": arduino_queue,
        "NetworkQueue": network_queue,
        "KeyboardQueue": input_queue,
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
            "chunk_duration": laughter_cfg.getfloat("chunk_duration"),
            "laughter_threshhold": laughter_cfg.getfloat("threshhold"),
            "records": laughter_cfg.getint("records"),
            "hits": laughter_cfg.getint("hits")
        })

    # Partials for convenience
    set_arduino_channel = partial(switch_channel, arduino_queue)
    event_handler = partial(
        handle_event,
        arduino_queue=arduino_queue,
        network_queue=network_queue,
        slower_tickle=game_cfg.getint("slower_tickle"),
        slow_tickle=game_cfg.getint("slow_tickle"),
        fast_tickle=game_cfg.getint("fast_tickle"),
        faster_tickle=game_cfg.getint("faster_tickle"),
        feather_channel=game_cfg.getint("feather_channel"),
        balloon_channel=game_cfg.getint("balloon_channel"),
        squeeze_duration=game_cfg.getfloat("squeeze_duration")
    )

    # Start and join all threads and processes
    expression_proc.start()
    expression_proc.join(0)
    laughter_proc.start()
    laughter_proc.join(0)
    kb_thread.start()
    kb_thread.join(0)
    arduino_thread.start()
    arduino_thread.join(0)
    network_thread.start()
    network_thread.join(0)

    # Main event loop
    while True:
        try:
            handle_ipc_recv(local_pipes, event_handler)
            handle_itc_recv(queues, event_handler)
            # handle_keyboard_input(input_queue)

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
        except GameOverException as e:
            print(box_strings("GAME OVER", e.args[0]))
            break

        # if not (expression_proc.is_alive() or laughter_proc.is_alive()):
            # break

    shutdown(local_pipes, queues)


def handle_ipc_recv(pipes: Pipes,
                    event_handler: EventHandler) -> None:
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
        elif isinstance(payload, EventEnum):
            event_handler(event=payload, location=LocationEnum.LOCAL)


def handle_itc_recv(queues: Queues,
                    event_handler: EventHandler) -> None:
    """Handle inter-thread communication in the receive direction."""
    global in_game
    for name, queue in queues.items():
        try:
            payload, other = queue.get(block=False)
            if name == "NetworkQueue" and other is DirectionEnum.SEND:
                queue.put(Payload(payload, other))
                continue
            if payload is ErrorEnum.SERIAL_ERROR:
                logger.error("Problem with the serial device.")
                raise SerialError
            elif payload is ErrorEnum.NETWORK_ERROR:
                logger.error("Problem with the network socket device.")
                raise NetworkError
            elif payload is CommandEnum.TERMINATE:
                raise UserTerminationException
            elif payload is CommandEnum.START:
                queues["NetworkQueue"].put(
                    Payload(EventEnum.START_GAME, DirectionEnum.SEND))
                in_game = True
                print("Good luck!")
            elif isinstance(payload, EventEnum):
                event_handler(event=payload,
                              location=(LocationEnum.REMOTE
                                        if name == "NetworkQueue"
                                        else LocationEnum.LOCAL))
            else:
                queue.put_nowait(Payload(payload, other))
        except Empty:
            continue


def handle_event(arduino_queue: ITCQueue,
                 network_queue: ITCQueue,
                 slower_tickle: int,
                 slow_tickle: int,
                 fast_tickle: int,
                 faster_tickle: int,
                 feather_channel: int,
                 balloon_channel: int,
                 squeeze_duration: float,
                 event: EventEnum,
                 location: LocationEnum) -> None:
    """Handle events."""
    global set_arduino_channel, in_game
    # print(f'Balloon={balloon_channel}, feather={feather_channel}')
    # print("Handling event:", event, location)
    if event is EventEnum.START_GAME:
        in_game = True
    elif not in_game:
        return
    if event is EventEnum.END_GAME and location is LocationEnum.REMOTE:
        raise UserTerminationException
    elif event is EventEnum.GAME_OVER:
        raise GameOverException("YOU WIN!" if location is LocationEnum.REMOTE
                                else "Better luck next time.")
    elif event is EventEnum.LAUGHTER_DETECTED:
        set_arduino_channel(channel=balloon_channel,
                            state=CommandEnum.CHANNEL_ON)
        time.sleep(squeeze_duration)
        network_queue.put(Payload(EventEnum.GAME_OVER, DirectionEnum.SEND))
        raise GameOverException("Better luck next time.")
    elif event is EventEnum.NO_LAUGHTER_DETECTED:
        # set_arduino_channel(channel=balloon_channel,
        #                     state=CommandEnum.CHANNEL_OFF)
        pass
    elif event in (EventEnum.NO_SMILE_DETECTED,
                   EventEnum.LOW_INTENSITY_SMILE_DETECTED,
                   EventEnum.MEDIUM_INTENSITY_SMILE_DETECTED,
                   EventEnum.HIGH_INTENSITY_SMILE_DETECTED):
        if location is LocationEnum.LOCAL:
            # print("Sending", network_queue.qsize())
            network_queue.put_nowait(Payload(event, DirectionEnum.SEND))
            # print(network_queue.qsize())
        elif location is LocationEnum.REMOTE:
            speed = 0
            if event is EventEnum.NO_SMILE_DETECTED:
                speed = slower_tickle
            elif event is EventEnum.LOW_INTENSITY_SMILE_DETECTED:
                speed = slow_tickle
            elif event is EventEnum.MEDIUM_INTENSITY_SMILE_DETECTED:
                speed = fast_tickle
            elif event is EventEnum.HIGH_INTENSITY_SMILE_DETECTED:
                speed = faster_tickle
            set_arduino_channel(channel=feather_channel,
                                state=CommandEnum.PULSE_CHANNEL,
                                interval=speed)


def shutdown(pipes: Pipes, queues: Queues) -> None:
    """Shutdown the game."""
    global set_arduino_channel, in_game
    # print("Shutting down.")
    for i in range(1, 5):
        set_arduino_channel(i, CommandEnum.PULSE_CHANNEL, 0)
        set_arduino_channel(i, CommandEnum.CHANNEL_OFF)
    for name, pipe in pipes.items():
        try:
            pipe.send(CommandEnum.TERMINATE)
        except (OSError, BrokenPipeError):
            continue
    for name, queue in queues.items():
        queue.put_nowait(Payload(CommandEnum.TERMINATE))
    in_game = False


def switch_channel(queue: ITCQueue,
                   channel: int,
                   state: CommandEnum,
                   interval: int = 0) -> None:
    """Set the arduino channel."""
    # print(f'Controling arduino: {channel!r} {state!r} {interval!r}')
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
        # print(f'Executing command: {state} {ch}')
        queue.put_nowait(Payload(state, ch))
    elif state == CommandEnum.PULSE_CHANNEL:
        # print(f'Executing: {state} {ch} {interval}')
        queue.put_nowait(Payload(state, (ch, interval)))
    else:
        return
