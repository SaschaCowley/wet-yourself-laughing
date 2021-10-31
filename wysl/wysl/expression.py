"""Expression detection game component."""

import multiprocessing as mp
from functools import partial
from multiprocessing.connection import Connection

import cv2
from fer import FER
from numpy import ndarray

from .enums import CommandEnum, ErrorEnum, EventEnum
from .exceptions import CameraError
from .types import ExpressionClassifier, FEREmotions, FERList

logger = mp.get_logger()


def expression_loop(pipe: Connection,
                    camera_index: int,
                    mtcnn: bool,
                    happy_weight: float,
                    surprise_weight: float,
                    low_threshhold: float,
                    medium_threshhold: float,
                    high_threshhold: float) -> None:
    """Expression detection loop.

    Args:
        pipe (Connection): IPC pipe for communicating with our parent process.
        camera_index (int): Index of the camera to use, as understood by
            opencv-python.
        mtcnn (bool): Whether or not to use MTCNN for face detection. Slower
            but more accurate.
        happy_weight (float): Weight to be used for the 'happy' expression when
            calculating the weighted average.
        surprise_weight (float): Weight to be used for the 'surprised'
            expression when calculating the weighted average.
        low_threshhold (float): Threshold that must be met or exceeded in order
            for an expression to be classified as a low intensity smile.
        medium_threshhold (float): Threshold that must be met or exceeded in
            order for an expression to be classified as a medium intensity
            smile.
        high_threshhold (float): Threshold that must be met or exceeded in
            order for an expression to be classified as a high intensity smile.
    """
    logger.info("Starting: %s", locals())

    # For later convenience.
    classifier = partial(classify_expression,
                         happy_weight=happy_weight,
                         surprise_weight=surprise_weight,
                         low_threshhold=low_threshhold,
                         medium_threshhold=medium_threshhold,
                         high_threshhold=high_threshhold)

    # Setup the camera feed and expression detector.
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
        except CameraError as e:
            logger.error(e.args)
            pipe.send(ErrorEnum.CAMERA_ERROR)

        try:
            pipe.send(emotions)
        except BrokenPipeError as e:
            logger.error(e.args)
            break

        if cv2.waitKey(1) == ord('q'):
            logger.info("Camera stream terminated by user.")
            pipe.send(CommandEnum.TERMINATE)
            break

    # Clean up after ourselves.
    cap.release()
    cv2.destroyAllWindows()
    pipe.close()


def get_emotions(
        cap: cv2.VideoCapture,
        detector: FER,
        classifier: ExpressionClassifier) -> EventEnum:
    """Capture a frame of video and extract emotions.

    Args:
        cap (cv2.VideoCapture): The video feed from which to draw frames.
        detector (FER): The FER instance to use to recognise expressions.
        classifier (ExpressionClassifier): Function to use to classify the
            expressions detected.

    Raises:
        CameraError: If there is an issue getting a frame from the video feed.

    Returns:
        EventEnum: EventEnum corresponding to the expression detected.
    """
    # Pull a frame of video.
    stat, frame = cap.read()
    if not stat:
        raise CameraError("Failed to read from camera.")

    ret = EventEnum.NO_SMILE_DETECTED  # Default state
    # Horizontal flip to make the displayed feed "mirror-like".
    frame = cv2.flip(frame, 1)
    emotions = detector.detect_emotions(frame)
    # If any faces were detected, classify the expression of the first one.
    if len(emotions) > 0:
        ret = classifier(emotions[0]['emotions'])

    # Display the frame and return the emotion detected.
    do_show(frame, emotions)
    return ret


def classify_expression(emotions: FEREmotions,
                        happy_weight: float,
                        surprise_weight: float,
                        low_threshhold: float,
                        medium_threshhold: float,
                        high_threshhold: float) -> EventEnum:
    """Classify emotions into no, low, medium, or high intensity smiles.

    Args:
        emotions (FEREmotions): Dictionary of emotions as returned by FER.
        happy_weight (float): Weight to be used for the 'happy' expression when
            calculating the weighted average.
        surprise_weight (float): Weight to be used for the 'surprised'
            expression when calculating the weighted average.
        low_threshhold (float): Threshold that must be met or exceeded in order
            for an expression to be classified as a low intensity smile.
        medium_threshhold (float): Threshold that must be met or exceeded in
            order for an expression to be classified as a medium intensity
            smile.
        high_threshhold (float): Threshold that must be met or exceeded in
            order for an expression to be classified as a high intensity smile.

    Returns:
        EventEnum: EventEnum according to the type of expression detected.
    """
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


def do_show(frame: ndarray, emotions_list: FERList) -> None:
    """Visually display the camera feed.

    Args:
        frame (ndarray): The frame to show, as a numpy array (this is how
            opencv-python returns them).
        emotions_list (FERList): List of the emotions as returned by FER.
    """
    if len(emotions_list) > 0:
        emotions = emotions_list[0]
        tl = emotions['box'][0:2]
        sz = emotions['box'][2:4]
        br = [tl[0]+sz[0], tl[1]+sz[1]]
        cv2.rectangle(frame, tl, br, (0, 155, 255), 5)
    cv2.imshow('Camera feed', frame)
