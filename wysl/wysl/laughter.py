"""Laughter detection component of the game."""

import audioop
from collections import deque
from multiprocessing.connection import Connection

import matplotlib.pyplot as plt
import numpy as np
import pyaudio
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon

from .enums import CommandEnum, StatusEnum

audio: pyaudio.PyAudio
stream: pyaudio.Stream
fig: Figure
ax: Axes
chunk_size: int
waveform: Line2D
sample_width: int
rms_rect: Polygon
recent_hits: deque[int]
num_hits: int
hit_volume: float


def laughter_loop(pipe: Connection,
                  microphone_index: int = 0,
                  rate: int = 16000,
                  channels: int = 1,
                  width: int = 2,
                  chunk_duration: float = 0.05,
                  mean: float = 200.0,
                  stddev: float = 240.0,
                  records: int = 10,
                  hits: int = 5) -> None:
    """Laughter detection loop."""
    global audio, stream, chunk_size, fig, ax, waveform, sample_width,\
        rms_rect, recent_hits, num_hits, hit_volume
    chunk_size = int(rate/(1/chunk_duration))
    sample_width = width
    num_hits = hits
    hit_volume = mean+3*stddev
    recent_hits = deque(maxlen=records)
    audio = pyaudio.PyAudio()
    stream = audio.open(rate=rate,
                        channels=channels,
                        format=pyaudio.get_format_from_width(width),
                        input=True, output=True,
                        input_device_index=microphone_index,
                        frames_per_buffer=chunk_size, start=False)
    plt.ioff()
    fig, ax = plt.subplots()
    ax.axhspan(-10000, 10000, fill=False, linestyle='dotted')
    rms_rect = ax.axhspan(0, 0, fill=False)
    waveform, = ax.plot(np.arange(chunk_size), np.zeros(chunk_size))
    print(type(waveform))
    ax.set_xlim(0, chunk_size-1)
    ax.set_ylim(-(2**(8*width))/2, (2**(8*width))/2)
    ax.set_title("Raw Audio Signal")
    plt.tight_layout()
    plt.show(block=False)
    pipe.send("Hello from the laughter loop!")
    stream.start_stream()
    while True:
        if pipe.poll(0):
            payload = pipe.recv()
            if payload == CommandEnum.TERMINATE:
                break
        stat = detect_laughter()
        fig.canvas.draw_idle()
        fig.canvas.flush_events()
        if stat:
            pipe.send(StatusEnum.LAUGHTER_DETECTED)

    plt.close('all')
    stream.stop_stream()
    stream.close()
    audio.terminate()


def detect_laughter() -> bool:
    """Detect laughter, draw graph, and return."""
    global stream, ax, chunk_size, waveform, sample_width, rms_rect,\
        recent_hits, num_hits, hit_volume
    in_data = stream.read(chunk_size)
    amplitude = np.fromstring(in_data, np.int16)
    volume = audioop.rms(in_data, sample_width)
    recent_hits.append(volume >= hit_volume)
    waveform.set_ydata(amplitude)
    rms_rect.remove()
    rms_rect = ax.axhspan(-volume, volume, fill=False)
    stream.write(in_data)
    return (len(recent_hits) == recent_hits.maxlen) \
        and (recent_hits.count(True) == num_hits)
