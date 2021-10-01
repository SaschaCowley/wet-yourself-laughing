from collections import namedtuple

import cv2
import pyaudio

from .utils import elicit_int

Camera = namedtuple('Camera', ('port', 'width', 'height', 'frame_rate'))
Microphone = namedtuple(
    'Microphone', ('port', 'name', 'sample_rate', 'channels'))


def setup(config):
    print(config)
    config["camera"] = select_camera()
    config["microphone"] = select_microphone()
    print(config)
    return config


def select_camera(default=0):
    print("Select which camera to use")
    working, available = get_cameras()
    for i, camera in enumerate(working):
        print(f'{i}  Port {camera.port}, '
              f'{camera.width:.0f}x{camera.height:.0f}, '
              f'{camera.frame_rate:.1f}fps')
    camera = elicit_int(f'Camera (default {default}): ', values=range(
        len(working)), default=default)
    return camera


def get_cameras():
    working = True
    port = 0
    working_ports = []
    available_ports = []
    while working:
        cap = cv2.VideoCapture(port)
        if not cap.isOpened():
            working = False
        else:
            reading, _ = cap.read()
            camera = Camera(
                port=port,
                width=cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                height=cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                frame_rate=cap.get(cv2.CAP_PROP_FPS)
            )
            if reading:
                working_ports.append(camera)
            else:
                available_ports.append(camera)
        cap.release()
        port += 1
    return working_ports, available_ports


def select_microphone(default=0):
    microphones = get_microphones()
    for i, microphone in enumerate(microphones):
        print(f'{i}  {microphone.name:<40.40}\t'
              f'{microphone.sample_rate:.0f}hz, '
              f'{microphone.channels} channels')
    microphone = elicit_int(f'Microphone (default {default}): ', values=range(
        len(microphones)), default=default)
    return microphones[microphone].port


def get_microphones():
    p = pyaudio.PyAudio()
    microphones = []
    for i in range(p.get_device_count()):
        device = p.get_device_info_by_index(i)
        if device['maxInputChannels'] > 0:
            microphones.append(Microphone(
                port=i,
                name=device['name'],
                sample_rate=device['defaultSampleRate'],
                channels=device['maxInputChannels']
            ))
    return microphones
