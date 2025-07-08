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
    def __init__(self, initialRoiFile : str, videoFile : str, roiCenter : Point, roiSize : Size):
        # Error checking
        if not os.path.isfile(initialRoiFile):
            print(f"Error: {initialRoiFile} not found")
            exit()
        if not os.path.isfile(videoFile):
            print(f"Error: {videoFile} not found")
            exit()

        self.videoFile = videoFile
        self.video = cv.VideoCapture(videoFile)
        self.frameNumber = 1 
        if not self.video.isOpened():
            print(f"Could not open {videoFile}")
            exit(-1)

        # initialize class member variables provided by client
        self.initialRoiFile = initialRoiFile
        self.videoFile      = videoFile
        self.origCenter     = roiCenter
        self.curCenter      = copy.copy(roiCenter)
        self.origRoiRect    = Rect(roiCenter.x - int(roiSize.w/2), roiCenter.y - int(roiSize.h/2), roiSize.w, roiSize.h)
        self.curRoiRect     = copy.copy(self.origRoiRect)

        # Use initialRoiFile to create initial ROI
        roiImage = cv.imread  (self.initialRoiFile, cv.IMREAD_COLOR)

        fourcc = cv.VideoWriter_fourcc(*'mp4v') # Or 'mp4v', 'MJPG' etc.
        self.videoOut = cv.VideoWriter('output.mp4', fourcc, 15.0, (roiImage.shape[1], roiImage.shape[0]), True)

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
        cv.circle(annotatedFrame, (roiCenter.x, roiCenter.y), 1, (255, 0, 255), 3)
        cv.imshow('Initial ROI', annotatedFrame) # Display the full ROI ultrasound image with a rectangle over the ROI
        
    # Find the ROI in the next video frame and draw the frame with the annotated ROI using the Tracker
    def processNextFrame(self):
        ret, newFrame = self.video.read() # Read a frame
        if not ret: # stream has ended
            print("End of video reached. Exiting after 5 seconds")
            self.release()
            cv.waitKey(5000) 
            cv.destroyAllWindows()
            exit()

        success,bbox=self.tracker.update(newFrame)  
        if success:
            self.curRoiRect.x = bbox[0]
            self.curRoiRect.y = bbox[1]

            # draw a yellow rect around the new ROI
            newAnnotatedFrame = cv.rectangle(newFrame, (bbox[0], bbox[1]), 
                                        (bbox[0] + roiRect.w, bbox[1] + roiRect.h), 
                                        (0, 255, 255), 1) 
            roiCenter = (int(bbox[0] + self.curRoiRect.w/2), int(bbox[1] + self.curRoiRect.h/2))
            cv.circle(newAnnotatedFrame, roiCenter, 1, (255, 0, 255), 3)

            # write the frame # onto the frame
            cv.putText(newAnnotatedFrame, f"Frame {self.frameNumber}", (5, 560), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv.LINE_AA)

            self.videoOut.write(newAnnotatedFrame)
            # Draw the new frame with the updated ROI rect and center
            cv.imshow(self.videoFile, newAnnotatedFrame) 
 

        else:
            newAnnotatedFrame = newFrame.copy()
            cv.putText(newFrame, f"Frame {self.frameNumber}: couldn't find ROI", (5, 560), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv.LINE_AA)
            cv.imshow('new Frame', newAnnotatedFrame) 

        self.frameNumber += 1
        return
 
    def release(self):
        self.videoOut.release()

if __name__ == "__main__":
    roiFile   = "../Scans/PreTreat_SagittalScroll-1.png"
    videoFile = "../Scans/PreTreat_SagittalScroll.avi"
    if len(sys.argv) > 2: 
        roiFile   = sys.argv[1]
        videoFile = sys.argv[2]

    # Extract the human-determined ROI (prostate) from full ROI U/S frame
    roiCenterX, roiCenterY = 518, 322
    roiSize = 200 #190  # square ROI rectangle for now

    trackRoi = TrackRoi(roiFile, videoFile, Point(roiCenterX, roiCenterY), Size(roiSize, roiSize))

    roiW, roiH  = roiSize, roiSize
    roiRect     = Rect(int(roiCenterX - roiW/2), int(roiCenterY - roiH/2), roiW, roiH)
    origRoiRect = copy.copy(roiRect)

    video = cv.VideoCapture(videoFile)
    if not video.isOpened():
        print("empty video, exiting...")
        exit(-1)

    while True:
        trackRoi.processNextFrame()
        if cv.waitKey(25) & 0xFF == ord('q'):
            trackRoi.release()
            video.release()
            cv.destroyAllWindows()
            exit()
        