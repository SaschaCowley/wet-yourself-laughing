"""Expression detection game component."""

from fer import FER
import cv2
from .enums import StatusEnum, CommandEnum
from .utils import ExpressionPayload
import multiprocessing as mp
from typing import Union

NullableExpressionPayload = Union[ExpressionPayload, None]
logger = mp.get_logger()
cap: cv2.VideoCapture
detector: FER


def expression_loop(pipe: mp.connection.Connection,
                    camera_index: int = 0,
                    mtcnn: bool = False) -> None:
    """Expression detection loop."""
    global cap, detector
    logger.debug(f'Camera index: {camera_index}; mtcnn: {mtcnn}')
    detector = FER(mtcnn=mtcnn)
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        logger.error(f'Failed to open stream {camera_index}')
        pipe.send(StatusEnum.CAMERA_ERROR)
        exit()

    while True:
        # pipe.send((0.5,0.8))
        if pipe.poll(0):
            payload = pipe.recv()
            if payload == CommandEnum.TERMINATE:
                break
        try:
            emotions = get_emotions()
            if emotions is not None:
                pipe.send(emotions)
        except RuntimeError as e:
            logger.error(e.args)

        if cv2.waitKey(1) == ord('q'):
            logger.info("Camera stream terminated by user.")
            break

    cap.release()
    cv2.destroyAllWindows()


def get_emotions() -> NullableExpressionPayload:
    global cap, detector
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Failed to read from camera.")
    frame = cv2.flip(frame, 1)
    emotions = detector.detect_emotions(frame)
    if len(emotions) == 0:
        return None
    emotions = emotions[0]
    tl = emotions['box'][0:2]
    sz = emotions['box'][2:4]
    br = [tl[0]+sz[0], tl[1]+sz[1]]
    cv2.rectangle(frame, tl, br, (255, 255, 255), 5)
    cv2.imshow('Camera feed', frame)
    return ExpressionPayload(happy=emotions['emotions']['happy'], surprise=emotions['emotions']['surprise'])
