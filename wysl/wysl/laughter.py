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
                  microphone_index: int = 0,
                  chunk_duration: float = 0.05,
                  laughter_threshhold: float = 2000,
                  records: int = 10,
                  hits: int = 5) -> None:
    """Laughter detection loop."""
    global running
    width = 2
    rate = 16000
    channels = 1
    logger.debug(f"Starting: {locals()}")
    chunk_size = int(rate/(1/chunk_duration))
    recent_volumes: FloatDeque = deque(maxlen=records)
    audio = pyaudio.PyAudio()
    stream = audio.open(rate=rate,
                        channels=channels,
                        format=pyaudio.get_format_from_width(width),
                        input=True, output=True,
                        input_device_index=microphone_index,
                        frames_per_buffer=chunk_size, start=False)
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
        fig.canvas.draw_idle()
        fig.canvas.flush_events()
        pipe.send(stat)

    if not running:
        pipe.send(CommandEnum.TERMINATE)

    plt.close('all')
    stream.stop_stream()
    stream.close()
    audio.terminate()


def detect_laughter(stream: pyaudio.Stream,
                    chunk_size: int,
                    sample_width: int,
                    figure: Figure,
                    hit_volume: float,
                    num_hits: int, recent_volumes: FloatDeque) -> EventEnum:
    """Detect laughter, draw graph, and return."""
    in_data = stream.read(chunk_size)
    volume = audioop.rms(in_data, sample_width)
    recent_volumes.append(volume)
    stream.write(in_data)
    do_show(in_data, volume, figure)
    return classify_sound(recent_volumes, hit_volume, num_hits)


def classify_sound(volumes: FloatDeque,
                   hit_volume: float,
                   min_hits: int) -> EventEnum:
    """Classify recent volume samples."""
    if volumes.maxlen is not None and len(volumes) < volumes.maxlen:
        return EventEnum.NO_LAUGHTER_DETECTED
    hits = [volume >= hit_volume for volume in volumes].count(True)
    if hits >= min_hits:
        return EventEnum.LAUGHTER_DETECTED
    else:
        return EventEnum.NO_LAUGHTER_DETECTED


def do_show(frame: bytes, rms: float, figure: Figure) -> None:
    """Visually display microphone feed."""
    ax = figure.gca()
    amplitudes = np.fromstring(frame, np.int16)
    for child in ax.get_children():
        label = child.get_label()
        if label == "Volume":
            child.remove()
        elif label == "Waveform":
            child.set_ydata(amplitudes)
    ax.axhspan(-rms, rms, fill=False, label="Volume")


def figure_close(event: CloseEvent) -> None:
    """Detect when the waveform window has been closed."""
    global running
    running = False
