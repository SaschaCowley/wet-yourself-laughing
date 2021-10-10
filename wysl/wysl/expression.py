"""Expression detection game component."""

import multiprocessing as mp
from multiprocessing.connection import Connection

import cv2
from fer import FER

from .enums import CommandEnum, StatusEnum
from .exceptions import CameraError
from .types import FEREmotions, FERDict
from numpy import ndarray
logger = mp.get_logger()
detector: FER


def expression_loop(pipe: Connection,
                    camera_index: int = 0,
                    mtcnn: bool = False) -> None:
    """Expression detection loop."""
    logger.debug(f'Camera index: {camera_index}; mtcnn: {mtcnn}')
    detector = FER(mtcnn=mtcnn, compile=True)
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        logger.error(f'Failed to open stream {camera_index}')
        pipe.send(StatusEnum.CAMERA_ERROR)
        exit()

    while True:
        if pipe.poll(0):
            payload = pipe.recv()
            if payload == CommandEnum.TERMINATE:
                break

        try:
            emotions = get_emotions(cap, detector)
            pipe.send(emotions)
        except CameraError as e:
            logger.error(e.args)
            pipe.send(StatusEnum.CAMERA_ERROR)
            break

        if cv2.waitKey(1) == ord('q'):
            logger.info("Camera stream terminated by user.")
            pipe.send(CommandEnum.TERMINATE)
            break

    cap.release()
    cv2.destroyAllWindows()
    pipe.close()


def get_emotions(cap: cv2.VideoCapture, detector: FER) -> StatusEnum:
    """Capture a frame of video and extract emotions."""
    stat, frame = cap.read()
    if not stat:
        raise CameraError("Failed to read from camera.")
    ret = StatusEnum.NO_SMILE_DETECTED
    frame = cv2.flip(frame, 1)
    emotions = detector.detect_emotions(frame)
    if len(emotions) > 0:
        ret = classify_expression(emotions[0]['emotions'])
    do_show(frame, emotions)
    return ret


def classify_expression(emotions: FEREmotions,
                        happy_weight: float = 1,
                        surprise_weight: float = 1,
                        low_threshhold: float = 0.4,
                        medium_threshhold: float = 0.6,
                        high_threshhold: float = 0.8) -> StatusEnum:
    """Classify emotions into no, low, medium, or high intensity smiles."""
    weighted_average = ((emotions['happy']*happy_weight
                         + emotions['surprise'] * surprise_weight)
                        / (happy_weight + surprise_weight))
    if weighted_average < low_threshhold:
        return StatusEnum.NO_SMILE_DETECTED
    elif weighted_average < medium_threshhold:
        return StatusEnum.LOW_INTENSITY_SMILE_DETECTED
    elif weighted_average < high_threshhold:
        return StatusEnum.MEDIUM_INTENSITY_SMILE_DETECTED
    else:
        return StatusEnum.HIGH_INTENSITY_SMILE_DETECTED


def do_show(frame: ndarray, emotions_list: list[FERDict]) -> None:
    """Visually display camera feed."""
    if len(emotions_list) > 0:
        emotions = emotions_list[0]
        tl = emotions['box'][0:2]
        sz = emotions['box'][2:4]
        br = [tl[0]+sz[0], tl[1]+sz[1]]
        cv2.rectangle(frame, tl, br, (0, 155, 255), 5)
    cv2.imshow('Camera feed', frame)
