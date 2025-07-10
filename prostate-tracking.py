# Track a user-specified region of interest as it moves in the ultrasoud video
# 
# Copyright 2025 InnerOptic Technology, Inc.
# Brian Heaney
import os
import sys
import copy
#import time
import cv2 as cv
import numpy as np
#from functools import partial
from random import randint
import tkinter as tk
from tkinter import filedialog

ESC = 27
def selectFile() -> str:
    # Create a root Tkinter window (it will be hidden)
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Open the file selection dialog
    selectedFile = filedialog.askopenfilename(
        title="Select a file",
        filetypes=(
            ("AVI files", "*.avi"),
            ("MP4 files", "*.mp4")
        )
    )

    # Destroy the root window after the dialog is closed
    root.destroy()

    if selectedFile:
        print(f"Selected file: {selectedFile}")
    else:
        print("No file selected.")

    return selectedFile

class Point:
    def __init__(self, x : int, y : int):
        self.x = x
        self.y = y

class Size:
    def __init__(self, w : int, h : int):
        self.w = w
        self.h = h
        
class Rect:
    def __init__(self, x : int, y : int, w : int, h : int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

# Class that tracks the ROI rectangle through the video 
# The ROI rectangle is defined by a roiSizexroiSize square located at roiCenter in the initialRoiFile image
class TrackRoi:
    def onMouseEvent(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            self.roiSelected = True
            self.origCenter = Point(x,y)


    def __init__(self, videoFile : str):
        self.video = cv.VideoCapture(videoFile)
        if not self.video.isOpened():
            print(f"Could not open {videoFile}")
            exit(-1)

        self.videoFile = videoFile
        self.frameNumber = 0
        self.frames = []
        self.forward = True
 
        # Use frame #0 to create initial ROI
        ret, frame0 = self.video.read()
        if not ret:
            print(f"Couldn't read frame 0 in {videoFile}")
            exit()

        self.video.set(cv.CAP_PROP_POS_FRAMES, 0)

        # Have the user select the center of the ROI
        bboxes = []
        while True:
            # draw bounding boxes over objects
            # selectROI's default behaviour is to draw box starting from the center
            # when fromCenter is set to false, you can draw box starting from top left corner
            bbox = cv.selectROI(f'Select ROIs in {videoFile}', frame0, fromCenter=True, printNotice=True, showCrosshair=True)
            bboxes.append(bbox)
            print("Press q or ESC to quit selecting boxes and start tracking")
            print("Press any other key to select next object")
            key = cv.waitKey(0) & 0xFF
            if key == ord('q') or key == ESC:
                break

        print('Selected bounding boxes {}'.format(bboxes))
        roiRect   = Rect(bboxes[0][0], bboxes[0][1], bboxes[0][2], bboxes[0][3])
        roiCenter = Point(int(roiRect.x + 0.5 + roiRect.w / 2), 
                          int(roiRect.y + 0.5 + roiRect.h / 2))

        #self.curRoiRect     = copy.copy(self.origRoiRect)

        # create the output video file
        fourcc = cv.VideoWriter_fourcc(*'mp4v') # Or 'mp4v', 'MJPG' etc.
        dot = videoFile.rfind('.')
        slash = videoFile.rfind('/')
        filename = videoFile[slash+1:dot]
        self.videoOut = cv.VideoWriter(f'{filename}.mp4', fourcc, 15.0, (frame0.shape[1], frame0.shape[0]), True)

        # Set up the tracker using the Kernelized Correlations Filter tracker 
        # NOTE: KCF requires a 3-color (BGR) image. Crashes with a gray image
        self.tracker = cv.TrackerKCF.create()
        self.tracker.init(frame0, (roiRect.x, roiRect.y, roiRect.w, roiRect.h))

        # Draw a red rect around the ROI and a magenta circle at the ROI center in the full u/s frame
        #annotatedFrame = copy.copy(frame0)
        annotatedFrame = cv.rectangle(frame0, 
                                      (roiRect.x            , roiRect.y), 
                                      (roiRect.x + roiRect.w, roiRect.y + roiRect.h), 
                                      (0, 0, 255), 1) 
        cv.circle(annotatedFrame, (roiCenter.x, roiCenter.y), 1, (255, 0, 255), 3)
        cv.imshow("ROI", annotatedFrame) # Display the full ROI ultrasound image with a rectangle over the ROI
        
    # Find the ROI in the next video frame and draw the frame with the annotated ROI using the Tracker
    def processNextFrame(self):
        if self.forward:
            ret, newFrame = self.video.read() # Read a frame
            if ret: 
                self.frames.append(newFrame.copy())
            else:
                print("End of video reached. Reversing playback direction")
                self.forward = False
                self.frameNumber -= 2

        if not self.forward:
            newFrame = self.frames[self.frameNumber]

        success,bbox=self.tracker.update(newFrame)  
        if success:
            roiRect = Rect(bbox[0], bbox[1], bbox[2], bbox[3])

            # draw a yellow rect around the new ROI
            newAnnotatedFrame = cv.rectangle(newFrame, (roiRect.x, roiRect.y), 
                                        (roiRect.x + roiRect.w, roiRect.y + roiRect.h), 
                                        (0, 255, 255), 1) 
            roiCenter = (int(roiRect.x + roiRect.w/2), int(roiRect.y + roiRect.h/2))
            cv.circle(newAnnotatedFrame, roiCenter, 1, (255, 0, 255), 3)

            # write the frame # onto the frame
            cv.putText(newAnnotatedFrame, f"Frame {self.frameNumber}", (5, 560), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv.LINE_AA)
 
        else:
            newAnnotatedFrame = newFrame.copy()
            cv.putText(newAnnotatedFrame, f"Frame {self.frameNumber}: couldn't find ROI", (5, 560), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv.LINE_AA)

        # Draw the new frame with the updated ROI rect and center, if found
        cv.imshow(self.videoFile, newAnnotatedFrame) 
    
        self.videoOut.write(newAnnotatedFrame)
        if self.forward:
            self.frameNumber += 1
        else:
            self.frameNumber -= 1
            if self.frameNumber < 0:
                self.release()
                exit()
        return
 
    def release(self):
        self.video.release()
        self.videoOut.release()

if __name__ == "__main__":
    if len(sys.argv) > 1: 
        videoFile = sys.argv[1]
    else:
        videoFile = selectFile()

    if not os.path.isfile(videoFile):
        print(f"Error: {videoFile} not found")
        exit()

    trackRoi = TrackRoi(videoFile)

    while True:
        key = cv.waitKey(25) & 0xFF
        trackRoi.processNextFrame()
        if key == ord('q') or key == ESC:
            trackRoi.release()
            cv.destroyAllWindows()
            cv.waitKey(4000)
            exit()
        