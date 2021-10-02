from collections import namedtuple
import cmd

import cv2
import pyaudio

from .utils import elicit_int

Camera = namedtuple('Camera', ('port', 'width', 'height', 'frame_rate'))
Microphone = namedtuple(
    'Microphone', ('port', 'name', 'sample_rate', 'channels'))


class ConfigCmd(cmd.Cmd):
    def __init__(self, configobj, *args, default=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._default = default
        self._configobj = configobj
        if default is not None:
            self.prompt += f' (default {default})'
        self.prompt += ": "

    def do_select(self, arg):
        raise NotImplementedError

    def do_test(self, arg):
        raise NotImplementedError

    def do_show(self, arg):
        """ Show the available options again. """
        raise NotImplementedError

    def default(self, arg):
        return self.do_select(arg)

    def emptyline(self):
        if self._default is not None:
            return self.do_select(self._default)
        else:
            return super().emptyline()


class SelectCamera(ConfigCmd):
    intro = '\nSelect which camera to use.'
    prompt = 'Camera'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cameras = get_cameras()
        self.intro += f'\n{self.stringify_cameras()}'

    def stringify_cameras(self):
        working, available = self.cameras
        return "\n".join(f'{i}  Port {camera.port}, '
                         f'{camera.width:.0f}x{camera.height:.0f}, '
                         f'{camera.frame_rate:.1f}fps'
                         for i, camera in enumerate(working))

    def validate_arg(self, arg):
        arg = int(arg)
        if arg not in range(len(self.cameras[0])):
            raise ValueError
        return arg

    def do_show(self, arg):
        """ Show the available cameras again. """
        print(self.stringify_cameras())

    def do_select(self, arg):
        """ Select which camera to use. """
        try:
            arg = self.validate_arg(arg)
            self._configobj["camera"] = arg
            return True
        except ValueError:
            print("You must enter a valid device number.")


class SelectMicrophone(ConfigCmd):
    intro = '\nSelect which microphone to use.'
    prompt = "Microphone"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.microphones = get_microphones()
        self.intro += f'\n{self.stringify_microphones()}'

    def stringify_microphones(self):
        microphones = self.microphones
        return "\n".join(f'{i}  {microphone.name:<40.40}\t'
                         f'{microphone.sample_rate:.0f}hz, '
                         f'{microphone.channels} channels'
                         for i, microphone in enumerate(microphones))

    def validate_arg(self, arg):
        arg = int(arg)
        if arg not in range(len(self.microphones)):
            raise ValueError
        return arg

    def do_show(self, arg):
        """ Show the available microphones again. """
        print(self.stringify_microphones())

    def do_select(self, arg):
        """ Select which microphone to use. """
        try:
            arg = self.validate_arg(arg)
            self._configobj["microphone"] = arg
            return True
        except ValueError:
            print("You must enter a valid device number.")


def setup(config):
    print(config)
    # config["camera"] = select_camera()
    SelectCamera(config, default=0).cmdloop()
    SelectMicrophone(config, default=0).cmdloop()
    # config["microphone"] = select_microphone()
    print(config)
    return config


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
