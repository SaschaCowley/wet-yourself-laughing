import cv2
from collections import namedtuple

Camera = namedtuple('Camera', ('port', 'width', 'height'))


def setup(config):
    print(config)
    config["camera"] = select_camera()
    #print("Input microphone: ")
    #print("IP address")
    #print("Port: ")
    print(config)
    return config


def select_camera(default=0):
    print("Select which camera to use")
    working, available = get_cameras()
    for i, camera in enumerate(working):
        print(f'{i}  Port {camera.port}, {camera.width}x{camera.height}')
    camera = None
    while camera is None:
        try:
            camera = input(f"Camera (default {default}): ").strip()
            if camera == "":
                camera = default
            else:
                camera = int(camera)
            if camera not in range(len(working)):
                raise ValueError
        except ValueError:
            print("You must enter a valid camera from the list above.")
            camera = None
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
                height=cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            )
            if reading:
                working_ports.append(camera)
            else:
                available_ports.append(camera)
        cap.release()
        port += 1
    return working_ports, available_ports
