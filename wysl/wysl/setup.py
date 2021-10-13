"""Setup component of the game."""

import cmd
from collections import namedtuple
from configparser import ConfigParser
from typing import Any, Optional
from serial.tools.list_ports import comports
import serial
import audioop
import statistics
import cv2
import pyaudio
import socket
from .utils import elicit_ipv4_address, elicit_float

Camera = namedtuple('Camera', ('port', 'width', 'height', 'frame_rate'))
Microphone = namedtuple(
    'Microphone', ('port', 'name', 'sample_rate', 'channels'))


class ConfigCmd(cmd.Cmd):
    """Configuration setter base class."""

    def __init__(self,
                 configobj: ConfigParser,
                 *args: Any,
                 section: str,
                 option: str,
                 default: Optional[str] = None,
                 **kwargs: Any) -> None:
        """Initialise the object."""
        super().__init__(*args, **kwargs)
        self._default = configobj.get(section, option, fallback=None)
        self._configobj = configobj
        self._section = section
        self._option = option
        if self._default is not None:
            self.prompt += f' (default {self._default})'
        self.prompt += ": "

    def do_select(self, arg: str) -> bool:
        """Select an option."""
        raise NotImplementedError

    def do_show(self, arg: str) -> None:
        """Show the available options again."""
        raise NotImplementedError

    def default(self, arg: str) -> Any:
        """Select the default option."""
        return self.do_select(arg)

    def emptyline(self) -> bool:
        """Select default."""
        if self._default is not None:
            return self.do_select(self._default)
        else:
            return super().emptyline()


class SelectArduino(ConfigCmd):
    """Class to enable selecting the Arduino port."""

    intro = '\nSelect the port to which the Arduino is connected.'
    prompt = 'Arduino'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialise the class."""
        super().__init__(*args, **kwargs)
        self.ports = comports()
        self.portnames = [port.name for port in self.ports]
        self.intro += f'\n{self.stringify_ports()}'

    def stringify_ports(self) -> str:
        """Convert list of ports to string."""
        return "\n".join(f'{port.name}: '
                         f'{port.description}'
                         for i, port in enumerate(self.ports))

    def validate_arg(self, arg: str) -> int:
        """Validate an argument."""
        arg = arg.strip()
        if arg not in self.portnames:
            raise ValueError
        return self.portnames.index(arg)

    def do_show(self, arg: str) -> None:
        """Show the available ports again."""
        print(self.stringify_ports())

    def do_select(self, arg: str) -> bool:
        """Select which port to use."""
        try:
            varg = self.validate_arg(arg)
            self._configobj.set(self._section, self._option,
                                self.ports[varg].device)
            return True
        except ValueError:
            print("You must enter a valid port name.")
            return False


class SelectCamera(ConfigCmd):
    """Class to enable selection of a camera stream."""

    intro = '\nSelect which camera to use.'
    prompt = 'Camera'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialise the object."""
        super().__init__(*args, **kwargs)
        self.cameras = get_cameras()
        self.intro += f'\n{self.stringify_cameras()}'

    def stringify_cameras(self) -> str:
        """Transform list of Camera objects to string."""
        working, available = self.cameras
        return "\n".join(f'{i}  Port {camera.port}, '
                         f'{camera.width:.0f}x{camera.height:.0f}, '
                         f'{camera.frame_rate:.1f}fps'
                         for i, camera in enumerate(working))

    def validate_arg(self, arg: str) -> int:
        """Validate an argument."""
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
            self._configobj.set(self._section, self._option, str(varg))
            return True
        except ValueError:
            print("You must enter a valid device number.")
            return False


class SelectMicrophone(ConfigCmd):
    """Class to enable selection of a microphone stream."""

    intro = '\nSelect which microphone to use.'
    prompt = "Microphone"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialise the object."""
        super().__init__(*args, **kwargs)
        self.microphones = get_microphones()
        self.intro += f'\n{self.stringify_microphones()}'

    def stringify_microphones(self) -> str:
        """Convert list of Microphone objects to string."""
        microphones = self.microphones
        return "\n".join(f'{i}  {microphone.name:<40.40}\t'
                         f'{microphone.sample_rate:.0f}hz, '
                         f'{microphone.channels} channels'
                         for i, microphone in enumerate(microphones))

    def validate_arg(self, arg: str) -> int:
        """Validate an argument."""
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
            self._configobj.set(self._section, self._option, str(varg))
            return True
        except ValueError:
            print("You must enter a valid device number.")
            return False


def setup(config: ConfigParser) -> ConfigParser:
    """Interactively configure some parts of the game."""
    print("Beginning the setup process.")
    SelectArduino(config, section="arduino", option="port").cmdloop()
    SelectCamera(config, section="expression", option="camera_index").cmdloop()
    SelectMicrophone(config, section="laughter",
                     option="microphone_index").cmdloop()
    config.set(
        "network", "remote_ip", elicit_ipv4_address(
            "Remote IP address", default=config.get(
                "network", "remote_ip", fallback=None)))
    config.set(
        "network", "local_ip", elicit_ipv4_address(
            "Local IP address", default=config.get(
                "network", "local_ip",
                fallback=socket.gethostbyname(socket.gethostname()))))
    mean, stddev = measure_noise(config.getint("laughter", "microphone_index"),
                                 config.get("arduino", "port"))
    config.set(
        "laughter", "threshhold", str(elicit_float(
            "Laughter threshhold", default=config.getfloat(
                "laughter", "threshhold",
                fallback=mean + 3*stddev))))

    print("Done. Other options may be set in config.ini.")
    return config


def get_cameras() -> tuple[list[Camera], list[Camera]]:
    """Get a list of cameras connected to this device."""
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
    """Get a list of microphones connected to this device."""
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
    """Test a camera stream."""
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
    """Test a microphone stream."""
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


def measure_noise(microphone_index: int,
                  arduino_port: str) -> tuple[float, float]:
    """Measure the noise levels."""
    chunk = 1024
    width = 2
    channels = 1
    rate = 16000
    record_seconds = 7

    volumes = []
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.get_format_from_width(width),
                    channels=channels, rate=rate, input=True,
                    frames_per_buffer=chunk,
                    input_device_index=microphone_index)
    ser = serial.Serial(port=arduino_port, baudrate=9600, timeout=0,
                        dsrdtr=True)

    print("Taking noise measurement...")

    ser.write(b'!A101!B211!C309!D401')
    for _ in range(int(rate/chunk*record_seconds)):
        data = stream.read(chunk)
        volumes.append(audioop.rms(data, width))
    ser.write(b'!A0!B0!C0!D0-A-B-C-D')

    print("Done.")

    ser.close()
    stream.stop_stream()
    stream.close()
    p.terminate()

    mean = statistics.mean(volumes[20:-20])
    stddev = statistics.stdev(volumes[20:-20])
    print(f'Mean: {mean}; Standard deviation: {stddev}')

    return mean, stddev
