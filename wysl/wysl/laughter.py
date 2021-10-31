"""Laughter detection component of the game."""

import audioop
import multiprocessing as mp
from collections import deque
from multiprocessing.connection import Connection

import matplotlib.pyplot as plt
import numpy as np
import pyaudio
from matplotlib.backend_bases import CloseEvent
from matplotlib.figure import Figure

from .enums import CommandEnum, EventEnum
from .types import FloatDeque

logger = mp.get_logger()
running: bool


def laughter_loop(pipe: Connection,
                  microphone_index: int,
                  chunk_duration: float,
                  laughter_threshhold: float,
                  records: int,
                  hits: int) -> None:
    """Laughter detection loop.

    Args:
        pipe (Connection): Pipe for communication with the parent process.
        microphone_index (int): Index of the input device to use, as
            understood by pyaudio.
        chunk_duration (float): Duration of audio segments.
        laughter_threshhold (float): Minimum volume required for a hit to be
            recorded.
        records (int): Number of recent volume records to keep.
        hits (int): Number of hits in recent records required to trigger
            laughter detection.
    """
    global running
    width = 2
    rate = 16000
    channels = 1
    logger.debug(f"Starting: {locals()}")
    # Setup audio things
    chunk_size = int(rate/(1/chunk_duration))
    recent_volumes: FloatDeque = deque(maxlen=records)
    audio = pyaudio.PyAudio()
    stream = audio.open(rate=rate,
                        channels=channels,
                        format=pyaudio.get_format_from_width(width),
                        input=True, output=True,
                        input_device_index=microphone_index,
                        frames_per_buffer=chunk_size, start=False)

    # Setup matplotlib things.
    plt.ioff()
    fig, ax = plt.subplots()
    ax.axhspan(
        -laughter_threshhold, laughter_threshhold, fill=False,
        linestyle='dotted', label="Threshhold")
    ax.plot(np.arange(chunk_size), np.zeros(chunk_size), label="Waveform")
    ax.set_xlim(0, chunk_size-1)
    ax.set_ylim(-(2**(8*width))/2, (2**(8*width))/2)
    ax.set_title("Raw Audio Signal")
    plt.tight_layout()
    fig.canvas.mpl_connect('close_event', figure_close)
    plt.show(block=False)

    # Start things going.
    stream.start_stream()
    running = True
    while running:
        if pipe.poll(0):
            payload = pipe.recv()
            if payload == CommandEnum.TERMINATE:
                break

        stat = detect_laughter(
            stream=stream, chunk_size=chunk_size, sample_width=width,
            figure=fig, hit_volume=laughter_threshhold, num_hits=hits,
            recent_volumes=recent_volumes)
        # Refresh the plot.
        fig.canvas.draw_idle()
        fig.canvas.flush_events()
        try:
            pipe.send(stat)
        except BrokenPipeError as e:
            logger.exception(e)
            break

    if not running:
        pipe.send(CommandEnum.TERMINATE)

    # Clean up after ourselves.
    plt.close('all')
    stream.stop_stream()
    stream.close()
    audio.terminate()


def detect_laughter(stream: pyaudio.Stream,
                    chunk_size: int,
                    sample_width: int,
                    figure: Figure,
                    hit_volume: float,
                    num_hits: int,
                    recent_volumes: FloatDeque) -> EventEnum:
    """Detect laughter, draw graph, and return.

    Args:
        stream (pyaudio.Stream): Audio stream from which to sample.
        chunk_size (int): Chunk size of buffer.
        sample_width (int): Sample width (16-bit etc).
        figure (Figure): Figure to which to plot the waveform.
        hit_volume (float): Minimum volume for a hit.
        num_hits (int): Number of hits required to trigger laughter detection.
        recent_volumes (FloatDeque): Deque of recently recorded volumes.

    Returns:
        EventEnum: EventEnum according to whether laughter has been detected or
            not.
    """
    in_data = stream.read(chunk_size)
    volume = audioop.rms(in_data, sample_width)
    recent_volumes.append(volume)
    stream.write(in_data)
    do_show(in_data, volume, figure)
    return classify_sound(recent_volumes, hit_volume, num_hits)


def classify_sound(volumes: FloatDeque,
                   hit_volume: float,
                   min_hits: int) -> EventEnum:
    """Classify recent volume samples.

    Args:
        volumes (FloatDeque): Deque of recently recorded volumes.
        hit_volume (float): Minimum volume in order for a hit to be recorded.
        min_hits (int): Minimum number of hits required for laughter detection.

    Returns:
        EventEnum: EventEnum.LAUGHTER_DETECTED or
            EventEnum.NO_LAUGHTER_DETECTED depending on whether laughter is
            detected or not.
    """
    # Only allow laughter detection when a full number of segments has been
    # collected.
    if volumes.maxlen is not None and len(volumes) < volumes.maxlen:
        return EventEnum.NO_LAUGHTER_DETECTED
    hits = [volume >= hit_volume for volume in volumes].count(True)
    if hits >= min_hits:
        return EventEnum.LAUGHTER_DETECTED
    return EventEnum.NO_LAUGHTER_DETECTED


def do_show(frame: bytes, rms: float, figure: Figure) -> None:
    """Visually display the waveform from the microphone feed.

    Args:
        frame (bytes): Latest audio frame ('segment') collected.
        rms (float): Volume (RMS) of this frame.n]
        figure (Figure): Figure on which to plot the waveform.
    """
    amplitudes = np.fromstring(frame, np.int16)
    ax = figure.gca()
    for child in ax.get_children():
        label = child.get_label()
        # Delete the volume polygon.
        if label == "Volume":
            child.remove()
        # Replace the data in the waveform.
        elif label == "Waveform":
            child.set_ydata(amplitudes)
    # Add a new volume polygon.
    ax.axhspan(-rms, rms, fill=False, label="Volume")


def figure_close(event: CloseEvent) -> None:
    """Detect when the waveform window has been closed."""
    global running
    running = False
