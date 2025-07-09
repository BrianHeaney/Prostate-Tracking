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
from functools import partial

import tkinter as tk
from tkinter import filedialog

def selectFile() -> str:
    # Create a root Tkinter window (it will be hidden)
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Open the file selection dialog
    selectedFile = filedialog.askopenfilename(
        title="Select a file",
        filetypes=(
            ("AVI files", "*.avi"),
            ("Text files", "*.txt"),
            ("Python files", "*.py"),
            ("All files", "*.*")
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


    def __init__(self, initialRoiFile : str, videoFile : str, roiCenter : Point, roiSize : Size):
        # Error checking
        if not os.path.isfile(initialRoiFile):
            print(f"Error: {initialRoiFile} not found")
            exit()
        if not os.path.isfile(videoFile):
            print(f"Error: {videoFile} not found")
            exit()

        self.videoFile = videoFile

        self.videoFile = selectFile()
        self.video = cv.VideoCapture(videoFile)
        self.frameNumber = 1 
        self.frames = []
        self.forward = True

        if not self.video.isOpened():
            print(f"Could not open {videoFile}")
            exit(-1)

        # initialize class member variables provided by client
        self.initialRoiFile = initialRoiFile

        # Use initialRoiFile to create initial ROI
        roiImage = cv.imread(self.initialRoiFile, cv.IMREAD_COLOR)

        self.origCenter     = roiCenter #default
        # Have the user select the center of the ROI
        roiSelectionImage = 'ROI Selection Frame'
        cv.namedWindow(roiSelectionImage)
        # have the user select the ROI center
        cv.setMouseCallback(roiSelectionImage, self.onMouseEvent)  
        self.roiSelected = False
        cv.imshow(roiSelectionImage, roiImage)
        while not self.roiSelected:
            key = cv.waitKey(25) & 0xFF

        #self.curCenter      = copy.copy(self.origCenter)
        self.origRoiRect    = Rect(self.origCenter.x - int(roiSize.w/2), self.origCenter.y - int(roiSize.h/2), roiSize.w, roiSize.h)
        self.curRoiRect     = copy.copy(self.origRoiRect)

        fourcc = cv.VideoWriter_fourcc(*'mp4v') # Or 'mp4v', 'MJPG' etc.
        dot = videoFile.rfind('.')
        slash = videoFile.rfind('/')
        filename = videoFile[slash+1:dot]
        self.videoOut = cv.VideoWriter(f'{filename}.mp4', fourcc, 15.0, (roiImage.shape[1], roiImage.shape[0]), True)

        # Set up the tracker using the Kernelized Correlations Filter tracker 
        self.tracker = cv.TrackerKCF.create()
        #self.tracker = cv.TrackerMIL.create()
        # NOTE: KCF requires a 3-color (BGR) image. Crashes with a gray image
        self.tracker.init(roiImage, (self.origRoiRect.x, self.origRoiRect.y, self.origRoiRect.w, self.origRoiRect.h))

        # Draw a red rect around the ROI and a magenta circle at the ROI center in the full u/s frame
        annotatedFrame = copy.copy(roiImage)
        annotatedFrame = cv.rectangle(annotatedFrame, 
                                        (self.origRoiRect.x                     , self.origRoiRect.y), 
                                        (self.origRoiRect.x + self.origRoiRect.w, self.origRoiRect.y + self.origRoiRect.h), 
                                        (0, 0, 255), 1) 
        cv.circle(annotatedFrame, (self.origCenter.x, self.origCenter.y), 1, (255, 0, 255), 3)
        cv.imshow(roiSelectionImage, annotatedFrame) # Display the full ROI ultrasound image with a rectangle over the ROI
        
    # Find the ROI in the next video frame and draw the frame with the annotated ROI using the Tracker
    def processNextFrame(self):
        if self.forward:
            ret, newFrame = self.video.read() # Read a frame
            if ret: 
                self.frames.append(newFrame.copy())
            else:
                print("End of video reached. Reversing playback directoin")
                self.forward = False
                self.frameNumber -= 2

        if not self.forward:
            newFrame = self.frames[self.frameNumber]

        success,bbox=self.tracker.update(newFrame)  
        if success:
            self.curRoiRect.x = bbox[0]
            self.curRoiRect.y = bbox[1]

            # draw a yellow rect around the new ROI
            newAnnotatedFrame = cv.rectangle(newFrame, (bbox[0], bbox[1]), 
                                        (bbox[0] + self.curRoiRect.w, bbox[1] + self.curRoiRect.h), 
                                        (0, 255, 255), 1) 
            roiCenter = (int(bbox[0] + self.curRoiRect.w/2), int(bbox[1] + self.curRoiRect.h/2))
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
    # roiFile   = "../Scans/PreTreat_SagittalScroll-1.png"
    # videoFile = "../Scans/PreTreat_SagittalScroll.avi"
    roiFile   = "../Scans/PreTreat_AxialScroll-0.png"
    videoFile = "../Scans/PreTreat_AxialScroll.avi"
    if len(sys.argv) > 2: 
        roiFile   = sys.argv[1]
        videoFile = sys.argv[2]

    # Extract the human-determined ROI (prostate) from full ROI U/S frame
    roiCenterX, roiCenterY = 689, 825  # apex in sagittal scan in PreTreat_SagittalScroll-1.png
    # roiCenterX, roiCenterY = 518, 322  # center of prostate in transverse scan in PreTreat_SagittalScroll-0.png
    # roiCenterX, roiCenterY = 500, 340  # center of prostate in transverse scan in PreTreat_AxialScroll-0.png
    roiCenterX, roiCenterY = 740, 770
    
    roiSize = 200 #190  # square ROI rectangle for now

    trackRoi = TrackRoi(roiFile, videoFile, Point(roiCenterX, roiCenterY), Size(roiSize, roiSize))

    while True:
        key = cv.waitKey(25) & 0xFF
        ESC = 27
        trackRoi.processNextFrame()
        if key == ord('q') or key == ESC:
            trackRoi.release()
            cv.destroyAllWindows()
            exit()
        