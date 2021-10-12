"""Setup component of the game."""

import cmd
from collections import namedtuple
from configparser import ConfigParser
from typing import Any, Optional

import cv2
import pyaudio

from .utils import elicit_int

Camera = namedtuple('Camera', ('port', 'width', 'height', 'frame_rate'))
Microphone = namedtuple(
    'Microphone', ('port', 'name', 'sample_rate', 'channels'))


class ConfigCmd(cmd.Cmd):
    def __init__(self,
                 configobj: ConfigParser,
                 *args: Any,
                 default: Optional[str] = None,
                 **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._default = default
        self._configobj = configobj
        if default is not None:
            self.prompt += f' (default {default})'
        self.prompt += ": "

    def do_select(self, arg: str) -> bool:
        raise NotImplementedError

    def do_show(self, arg: str) -> None:
        """Show the available options again."""
        raise NotImplementedError

    def default(self, arg: str) -> Any:
        return self.do_select(arg)

    def emptyline(self) -> bool:
        if self._default is not None:
            return self.do_select(self._default)
        else:
            return super().emptyline()


class SelectCamera(ConfigCmd):
    intro = '\nSelect which camera to use.'
    prompt = 'Camera'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.cameras = get_cameras()
        self.intro += f'\n{self.stringify_cameras()}'

    def stringify_cameras(self) -> str:
        working, available = self.cameras
        return "\n".join(f'{i}  Port {camera.port}, '
                         f'{camera.width:.0f}x{camera.height:.0f}, '
                         f'{camera.frame_rate:.1f}fps'
                         for i, camera in enumerate(working))

    def validate_arg(self, arg: str) -> int:
        iarg = int(arg)
        if iarg not in range(len(self.cameras[0])):
            raise ValueError
        return iarg

    def do_show(self, arg: str) -> None:
        """Show the available cameras again."""
        print(self.stringify_cameras())

    def do_test(self, arg: str) -> None:
        """Test a camera."""
        try:
            varg = self.validate_arg(arg)
            test_camera(varg)
        except ValueError:
            print("You must enter a valid device number.")

    def do_select(self, arg: str) -> bool:
        """Select which camera to use."""
        try:
            varg = self.validate_arg(arg)
            self._configobj["expression"]["camera_index"] = str(varg)
            return True
        except ValueError:
            print("You must enter a valid device number.")
            return False


class SelectMicrophone(ConfigCmd):
    intro = '\nSelect which microphone to use.'
    prompt = "Microphone"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.microphones = get_microphones()
        self.intro += f'\n{self.stringify_microphones()}'

    def stringify_microphones(self) -> str:
        microphones = self.microphones
        return "\n".join(f'{i}  {microphone.name:<40.40}\t'
                         f'{microphone.sample_rate:.0f}hz, '
                         f'{microphone.channels} channels'
                         for i, microphone in enumerate(microphones))

    def validate_arg(self, arg: str) -> int:
        iarg = int(arg)
        if iarg not in range(len(self.microphones)):
            raise ValueError
        return iarg

    def do_test(self, arg: str) -> None:
        """Select which microphone to use."""
        try:
            varg = self.validate_arg(arg)
            test_microphone(varg)
        except ValueError:
            print("You must enter a valid device number.")

    def do_show(self, arg: str) -> None:
        """Show the available microphones again."""
        print(self.stringify_microphones())

    def do_select(self, arg: str) -> bool:
        """Select which microphone to use."""
        try:
            varg = self.validate_arg(arg)
            self._configobj["laughter"]["microphone_index"] = str(varg)
            return True
        except ValueError:
            print("You must enter a valid device number.")
            return False


def setup(config: ConfigParser) -> ConfigParser:
    print(config)
    # config["camera"] = select_camera()
    SelectCamera(config, default=0).cmdloop()
    SelectMicrophone(config, default=0).cmdloop()
    # config["microphone"] = select_microphone()
    print(config)
    return config


def get_cameras() -> tuple[list[Camera], list[Camera]]:
    working = True
    port = 0
    working_ports = []
    available_ports = []
    while working:
        cap = cv2.VideoCapture(port, cv2.CAP_DSHOW)
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


def get_microphones() -> list[Microphone]:
    p = pyaudio.PyAudio()
    microphones = []
    for i in range(p.get_device_count()):
        device = p.get_device_info_by_index(i)
        if int(device['maxInputChannels']) > 0:
            microphones.append(Microphone(
                port=i,
                name=device['name'],
                sample_rate=device['defaultSampleRate'],
                channels=device['maxInputChannels']
            ))
    p.terminate()
    return microphones


def test_camera(index: int) -> None:
    print("(Press Ctrl+C to stop.)")
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Error opening stream.")
        return
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            cv2.imshow('Camera stream', frame)
            if cv2.waitKey(1) == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    cap.release()
    cv2.destroyAllWindows()


def test_microphone(index: int) -> None:
    print("(Press Ctrl+C to stop.)")
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.get_format_from_width(2), channels=1,
                    rate=16000, input=True, output=True,
                    frames_per_buffer=1024, input_device_index=index)
    try:
        while True:
            data = stream.read(1024)
            stream.write(data, 1024)
    except KeyboardInterrupt:
        pass
    stream.stop_stream()
    stream.close()
    p.terminate()
