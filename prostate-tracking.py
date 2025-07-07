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

        self.searchWindow = 10   # +/- pixels around the ROI rect to search for the best match
 
        self.enableFiltering = False
        self.blur   = 5
        self.alpha  = 2.8
        self.beta   = -4.9
        self.thresh = 90
        self.maxval = 255

        # read the ROI image file and crop the ROI rect into roiImage
        roiFullImage = cv.imread  (self.initialRoiFile, cv.IMREAD_COLOR)
        roiGrayImage = cv.cvtColor(roiFullImage, cv.COLOR_BGR2GRAY)
        self.origRoiImage = roiGrayImage[self.origRoiRect.y:self.origRoiRect.y+self.origRoiRect.h, 
                                         self.origRoiRect.x:self.origRoiRect.x+self.origRoiRect.w]

        self.curRoiImage = self.filterImage(self.origRoiImage)

        # Set up the tracker using the Kernelized Correlations Filter tracker 
        self.tracker = cv.TrackerMIL.create()
        self.tracker.init(roiGrayImage, (self.origRoiRect.x, self.origRoiRect.y, self.origRoiRect.w, self.origRoiRect.h))

        # Draw a red rect around the ROI and a magenta circle at the ROI center in the full u/s frame
        annotatedRoiFrame = copy.copy(roiFullImage)
        annotatedRoiFrame = cv.rectangle(annotatedRoiFrame, 
                                        (self.origRoiRect.x                     , self.origRoiRect.y), 
                                        (self.origRoiRect.x + self.origRoiRect.w, self.origRoiRect.y + self.origRoiRect.h), 
                                        (0, 0, 255), 1) 
        cv.circle(annotatedRoiFrame, (roiCenter.x, roiCenter.y), 1, (255, 0, 255), 3)
        cv.imshow('Annotated ROI Image', annotatedRoiFrame) # Display the full ROI ultrasound image with a rectangle over the ROI

    # Filter the image if self.enableFiltering is True
    def filterImage(self, image : np.array) -> np.array:
        if self.enableFiltering:
            blurImage          = cv.medianBlur(image, self.blur)
            equalizeImage      = cv.equalizeHist(blurImage)
            #contrastImage      = cv.convertScaleAbs(src=blurImage, alpha=self.alpha, beta=self.beta)
            ret,thresholdImage = cv.threshold(equalizeImage, self.thresh, self.maxval, cv.THRESH_BINARY)
            cv.imshow("Equalize" , equalizeImage)
            cv.imshow("Threshold", thresholdImage)
            return thresholdImage        
        else:
            return copy.copy(image)


        
    # Find the ROI in the next video frame and draw the frame with the annotated ROI
    def processNextFrame(self):
        ret, newFrame = self.video.read() # Read a frame
        if not ret: # If frame is not read correctly, stream has ended
            print("End of video reached. Exiting after 5 seconds")
            cv.waitKey(5000) 
            cv.destroyAllWindows()
            exit()

        newGrayFrame = cv.cvtColor(newFrame, cv.COLOR_BGR2GRAY)
        success,bbox=self.tracker.update(newGrayFrame)
        if success:
            self.curRoiRect.x = bbox[0]
            self.curRoiRect.y = bbox[1]
            self.curRoiImage  = newGrayFrame[bbox[1]:bbox[1]+self.curRoiRect.h, bbox[0]:bbox[0]+self.curRoiRect.w]
            cv.imshow("Cur ROI", self.curRoiImage)

            # draw a yellow rect around the new ROI
            newAnnotatedFrame = cv.rectangle(newFrame, (bbox[0], bbox[1]), 
                                        (bbox[0] + roiRect.w, bbox[1] + roiRect.h), 
                                        (0, 255, 255), 1) 
            roiCenter = (int(bbox[0] + self.curRoiRect.w/2), int(bbox[1] + self.curRoiRect.h/2))
            cv.circle(newAnnotatedFrame, roiCenter, 1, (255, 0, 255), 3)

            # write the frame # onto the frame
            cv.putText(newAnnotatedFrame, f"Frame {self.frameNumber}", (5, 560), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv.LINE_AA)

            # Draw the new frame with the updated ROI rect and center
            self.frameNumber += 1
            cv.imshow('new Frame', newAnnotatedFrame) 

            newGrayFrame = self.filterImage(newGrayFrame)
        else:
            newAnnotatedFrame = newFrame.copy()
            cv.putText(newFrame, f"Frame {self.frameNumber}: couldn't find ROI", (5, 560), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv.LINE_AA)
            cv.imshow('new Frame', newAnnotatedFrame) 
        return
        # Extract and display the transverse scan
        # x, y, w, h = 198, 91, 795, 453  
        # transverseImage = newGrayFrame[y:y+h, x:x+w]
        # cv.imshow('Transverse', transverseImage) 

        # Extract and display the sagittal scan
        # x, y, w, h = 198, y+h, 795, 464 
        # sagittalImage = newGrayFrame[y:y+h, x:x+w]
        # cv.imshow('Sagittal', sagittalImage) 

        # find the ROI in the current frame by moving the current ROI image around the searchWindox box to find the location with the smalled difference
        diffList = []
        index = minIndex = 0
        minErr = 0
        minX = minY = 0
        for x in range(self.curRoiRect.x - self.searchWindow, self.curRoiRect.x + self.searchWindow):
            for y in range(self.curRoiRect.y - self.searchWindow, self.curRoiRect.y + self.searchWindow):
                # extract the ROI rect from the new image, located at <x, y>
                testRoiImage = newGrayFrame[y:y+self.curRoiRect.h, x:x+self.curRoiRect.w]
                diff = cv.subtract(self.curRoiImage, testRoiImage)
                err = np.sum(diff**2)
                if index == 0 or err < minErr:
                    minIndex = index
                    minErr = err
                    minX = x
                    minY = y

                mse = err/(float(self.curRoiImage.size))
                #diffList.append((index, x, y, err, mse))
                index += 1

        # update the current ROI image and rectangle
        self.curRoiRect.x = minX
        self.curRoiRect.y = minY
        self.curRoiImage  = newGrayFrame[minY:minY+self.curRoiRect.h, minX:minX+self.curRoiRect.w]
        cv.imshow("Cur ROI", self.curRoiImage)

        # draw a yellow rect around the new ROI
        newAnnotatedFrame = cv.rectangle(newFrame, (minX, minY), 
                                    (minX + roiRect.w, minY + roiRect.h), 
                                    (0, 255, 255), 1) 
        roiCenter = (int(minX + self.curRoiRect.w/2), int(minY + self.curRoiRect.h/2))
        cv.circle(newAnnotatedFrame, roiCenter, 1, (255, 0, 255), 3)

        # write the frame # onto the frame
        cv.putText(newAnnotatedFrame, f"Frame {self.frameNumber}", (5, 560), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv.LINE_AA)

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
    roiCenterX, roiCenterY = 518, 322
    roiSize = 200 #190  # square ROI rectangle for now

    trackRoi = TrackRoi(roiFile, videoFile, Point(roiCenterX, roiCenterY), Size(roiSize, roiSize))

    roiW, roiH = roiSize, roiSize
    roiRect = Rect(int(roiCenterX - roiW/2), int(roiCenterY - roiH/2), roiW, roiH)
    origRoiRect = copy.copy(roiRect)

    video = cv.VideoCapture(videoFile)
    if not video.isOpened():
        print("empty video, exiting...")
        exit(-1)

    while True:
        trackRoi.processNextFrame()
        if cv.waitKey(25) & 0xFF == ord('q'):
            cv.destroyAllWindows()
            exit()
        