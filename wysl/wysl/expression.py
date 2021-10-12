"""Expression detection game component."""

import multiprocessing as mp
from multiprocessing.connection import Connection

import cv2
from fer import FER
from typing import Callable
from .enums import CommandEnum, EventEnum, ErrorEnum
from .exceptions import CameraError
from .types import FEREmotions, FERDict
from numpy import ndarray
from functools import partial

logger = mp.get_logger()

def expression_loop(pipe: Connection,
                    camera_index: int,
                    mtcnn: bool,
                    happy_weight: float,
                    surprise_weight: float,
                    low_threshhold: float,
                    medium_threshhold: float,
                    high_threshhold: float) -> None:
    """Expression detection loop."""
    logger.info("Starting: %s", locals())
    exit()
    classifier = partial(classify_expression,
                         happy_weight=happy_weight,
                         surprise_weight=surprise_weight,
                         low_threshhold=low_threshhold,
                         medium_threshhold=medium_threshhold,
                         high_threshhold=high_threshhold)
    detector = FER(mtcnn=mtcnn, compile=True)
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        logger.error(f'Failed to open stream {camera_index}')
        pipe.send(ErrorEnum.CAMERA_ERROR)
        exit()

    while True:
        if pipe.poll(0):
            payload = pipe.recv()
            if payload == CommandEnum.TERMINATE:
                break

        try:
            emotions = get_emotions(cap, detector, classifier)
            pipe.send(emotions)
        except CameraError as e:
            logger.error(e.args)
            pipe.send(ErrorEnum.CAMERA_ERROR)
            break

        if cv2.waitKey(1) == ord('q'):
            logger.info("Camera stream terminated by user.")
            pipe.send(CommandEnum.TERMINATE)
            break

    cap.release()
    cv2.destroyAllWindows()
    pipe.close()


def get_emotions(
        cap: cv2.VideoCapture,
        detector: FER,
        classifier: Callable[[FEREmotions], EventEnum]) -> EventEnum:
    """Capture a frame of video and extract emotions."""
    stat, frame = cap.read()
    if not stat:
        raise CameraError("Failed to read from camera.")
    ret = EventEnum.NO_SMILE_DETECTED
    frame = cv2.flip(frame, 1)
    emotions = detector.detect_emotions(frame)
    if len(emotions) > 0:
        ret = classifier(emotions[0]['emotions'])
    do_show(frame, emotions)
    return ret


def classify_expression(emotions: FEREmotions,
                        happy_weight: float,
                        surprise_weight: float,
                        low_threshhold: float,
                        medium_threshhold: float,
                        high_threshhold: float) -> EventEnum:
    """Classify emotions into no, low, medium, or high intensity smiles."""
    weighted_average = ((emotions['happy']*happy_weight
                         + emotions['surprise'] * surprise_weight)
                        / (happy_weight + surprise_weight))
    if weighted_average < low_threshhold:
        return EventEnum.NO_SMILE_DETECTED
    elif weighted_average < medium_threshhold:
        return EventEnum.LOW_INTENSITY_SMILE_DETECTED
    elif weighted_average < high_threshhold:
        return EventEnum.MEDIUM_INTENSITY_SMILE_DETECTED
    else:
        return EventEnum.HIGH_INTENSITY_SMILE_DETECTED


def do_show(frame: ndarray, emotions_list: list[FERDict]) -> None:
    """Visually display camera feed."""
    if len(emotions_list) > 0:
        emotions = emotions_list[0]
        tl = emotions['box'][0:2]
        sz = emotions['box'][2:4]
        br = [tl[0]+sz[0], tl[1]+sz[1]]
        cv2.rectangle(frame, tl, br, (0, 155, 255), 5)
    cv2.imshow('Camera feed', frame)
