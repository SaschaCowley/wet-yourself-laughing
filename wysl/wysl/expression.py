"""Expression detection game component."""

from fer import FER
import cv2
from .enums import Status
import sys


def expression_loop(pipe, camera_index):
    """Expression detection loop."""
    detector = FER()
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        pipe.send(Status.CAMERA_ERROR)
        exit()

    while True:
        ret, frame = cap.read()
        if not ret:
            pipe.send(Status.CAMERA_ERROR)
            break
        # frame = cv.flip(frame, 1)
        emotions = detector.detect_emotions(frame)
        # emo, wt = detector.top_emotion(frame)
        if len(emotions) > 0:
            tl = emotions[0]["box"][0:2]
            sz = emotions[0]["box"][2:4]
            br = [tl[0]+sz[0], tl[1]+sz[1]]
            # print(tl, br)
            cv2.rectangle(frame, tl, br, (255, 255, 255), 5)
            # cv.rectangle(frame, (0, 0), (640, 100), (0,0,0), -1)
            # cv.putText(frame, f'{emo} ({wt})', (0, 75), cv.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv.LINE_AA)
        # print(emotions)
        # out.write(frame)
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    sys.exit(0)
