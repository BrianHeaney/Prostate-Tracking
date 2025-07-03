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

        # read the ROI image file and crop the ROI rect into roiImage
        roiFullImage = cv.imread  (self.initialRoiFile, cv.IMREAD_COLOR)
        roiGrayImage = cv.cvtColor(roiFullImage, cv.COLOR_BGR2GRAY)
        self.origRoiImage = roiGrayImage[self.origRoiRect.y:self.origRoiRect.y+self.origRoiRect.h, 
                                         self.origRoiRect.x:self.origRoiRect.x+self.origRoiRect.w]
        self.curRoiImage  = copy.copy(self.origRoiImage)


        # Draw a red rect around the ROI and a magenta circle at the ROI center in the full u/s frame
        annotatedRoiFrame = copy.copy(roiFullImage)
        annotatedRoiFrame = cv.rectangle(annotatedRoiFrame, 
                                        (self.origRoiRect.x                     , self.origRoiRect.y), 
                                        (self.origRoiRect.x + self.origRoiRect.w, self.origRoiRect.y + self.origRoiRect.h), 
                                        (0, 0, 255), 1) 
        cv.circle(annotatedRoiFrame, (roiCenter.x, roiCenter.y), 1, (255, 0, 255), 3)
        cv.imshow('Annotated ROI Image', annotatedRoiFrame) # Display the full ROI ultrasound image with a rectangle over the ROI

    # Find the ROI in the next video frame and draw the frame with the annotated ROI
    def processNextFrame(self):
        ret, newFrame = self.video.read() # Read a frame
        if not ret: # If frame is not read correctly, stream has ended
            print("End of video reached. Exiting after 5 seconds")
            cv.waitKey(5000) 
            cv.destroyAllWindows()
            exit()

        # find the ROI in the current frame by moving the current ROI image around the searchWindox box to find the location with the smalled difference
        newGrayFrame = cv.cvtColor(newFrame, cv.COLOR_BGR2GRAY)
        searchWindow = 10   # num pixels around the ROI rect to search for a match
        diffList = []
        index = minIndex = 0
        minErr = 0
        minX = minY = 0
        for x in range(self.curRoiRect.x - searchWindow, self.curRoiRect.x + searchWindow):
            for y in range(self.curRoiRect.y - searchWindow, self.curRoiRect.y + searchWindow):
                # extract the ROI rect from the new image, located at <x, y>
                testRoiImage = newGrayFrame[y:y+self.curRoiRect.h, x:x+self.curRoiRect.w]
                diff = cv.subtract(self.curRoiImage, testRoiImage)
                err = np.sum(diff**2)
                if index == 0 or err < minErr:
                    minIndex = index
                    minErr = err
                    minX = x
                    minY = y

                mse = err/(float(roiImage.size))
                #diffList.append((index, x, y, err, mse))
                index += 1

        # update the current ROI image and rectangle
        self.curRoiRect.x = minX
        self.curRoiRect.y = minY
        self.curRoiImage  = newGrayFrame[minY:minY+self.curRoiRect.h, minX:minX+self.curRoiRect.w]

        # draw a yellow rect around the new ROI
        newAnnotatedFrame = cv.rectangle(newFrame, (minX, minY), 
                                    (minX + roiRect.w, minY + roiRect.h), 
                                    (0, 255, 255), 1) 
        roiCenter = (int(minX + self.curRoiRect.w/2), int(minY + self.curRoiRect.h/2))
        cv.circle(newAnnotatedFrame, roiCenter, 1, (255, 0, 255), 3)

        # write the frame # onto the frame
        text = f"Frame {self.frameNumber}"
        org = (5, 560)  # Bottom-left corner of the text
        fontFace = cv.FONT_HERSHEY_SIMPLEX
        fontScale = 1.0
        color = (0, 255, 0)  # Green color in BGR
        thickness = 2
        lineType = cv.LINE_AA
        cv.putText(newAnnotatedFrame, text, org, fontFace, fontScale, color, thickness, lineType)

        # Draw the new frame with the updated ROI rect and center
        self.frameNumber += 1
        cv.imshow('new Frame', newAnnotatedFrame) 


if __name__ == "__main__":
    roiFile   = "../Scans/PreTreat_SagittalScroll-1.png"
    videoFile = "../Scans/PreTreat_SagittalScroll.avi"
    if len(sys.argv) > 2: 
        roiFile   = sys.argv[1]
        videoFile = sys.argv[2]

    # Extract the human-determined ROI (prostate) from full ROI U/S frame
    roiCenterX, roiCenterY = 520, 325
    roiSize = 180  # square ROI rectangle for now

    trackRoi = TrackRoi(roiFile, videoFile, Point(roiCenterX, roiCenterY), Size(roiSize, roiSize))

    roiW, roiH = roiSize, roiSize
    roiRect = Rect(int(roiCenterX - roiW/2), int(roiCenterY - roiH/2), roiW, roiH)
    origRoiRect = copy.copy(roiRect)
    #x, y, w, h = 439, 226, 182, 195
    roiFrame     = cv.imread  (roiFile , cv.IMREAD_COLOR)
    roiGrayFrame = cv.cvtColor(roiFrame, cv.COLOR_BGR2GRAY)
    roiImage     = roiGrayFrame[roiRect.y:roiRect.y+roiRect.h, roiRect.x:roiRect.x+roiRect.w]
    originalRoiImage = copy.copy(roiImage)

    medianBlur = cv.medianBlur(roiImage, 5)   
    contrastImage = cv.convertScaleAbs(medianBlur, alpha=1.5, beta=0)
    ret,threshholdImage = cv.threshold(contrastImage,128,255,cv.THRESH_BINARY)
    cv.imshow("Threshold", threshholdImage)

    video = cv.VideoCapture(videoFile)
    if not video.isOpened():
        print("empty video, exiting...")
        exit(-1)

    while True:
        trackRoi.processNextFrame()
        if cv.waitKey(25) & 0xFF == ord('q'):
            cv.destroyAllWindows()
            exit()
        