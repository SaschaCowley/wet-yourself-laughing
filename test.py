import cv2 as cv
import numpy as np
import sys
from fer import FER
from time import perf_counter as pc

detector = FER(mtcnn=True)
cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Error opening stream.")
    exit()

#out = cv.VideoWriter('output.avi', cv.VideoWriter_fourcc(*'DIVX'), 25, (640, 480))

frames = 0
total = 0
while True:
    start = pc()
    ret, frame = cap.read()
    if not ret:
        break
    #frame = cv.flip(frame, 1)
    emotions = detector.detect_emotions(frame)
    #emo, wt = detector.top_emotion(frame)
    if len(emotions) > 0:
        tl = emotions[0]["box"][0:2]
        sz = emotions[0]["box"][2:4]
        br = [tl[0]+sz[0], tl[1]+sz[1]]
        # print(tl, br)
        cv.rectangle(frame, tl, br, (255, 255, 255), 5)
        #cv.rectangle(frame, (0, 0), (640, 100), (0,0,0), -1)
        #cv.putText(frame, f'{emo} ({wt})', (0, 75), cv.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv.LINE_AA)
    # print(emotions)
    #out.write(frame)
    cv.imshow('frame', frame)
    total += pc() - start
    frames += 1
    if cv.waitKey(1) == ord('q'):
        break

cap.release()
#out.release()
cv.destroyAllWindows()

print(f"Frames: {frames}\nTotal time: {total}\nFPS: {frames/total}")