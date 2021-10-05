"""Expression detection game component."""

from fer import FER
import cv2
from .enums import StatusEnum, CommandEnum
import multiprocessing as mp

logger = mp.get_logger()


def expression_loop(pipe, camera_index=0, mtcnn=False):
    """Expression detection loop."""
    logger.info(f'Camera index: {camera_index}; mtcnn: {mtcnn}')
    detector = FER(mtcnn=mtcnn)
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
        ret, frame = cap.read()
        if not ret:
            logger.error(f'Failed to read from stream {camera_index}')
            pipe.send(StatusEnum.CAMERA_ERROR)
            break
        frame = cv2.flip(frame, 1)
        emotions = detector.detect_emotions(frame)
        if len(emotions) > 0:
            tl = emotions[0]["box"][0:2]
            sz = emotions[0]["box"][2:4]
            br = [tl[0]+sz[0], tl[1]+sz[1]]
            # print(tl, br)
            cv2.rectangle(frame, tl, br, (255, 255, 255), 5)

        # print(emotions)
        # out.write(frame)
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) == ord('q'):
            logger.info("Camera stream terminated by user.")
            break

    cap.release()
    cv2.destroyAllWindows()
