# Track a region of interest as it moves in the ultrasoud video
# 
# Copyright 2025 InnerOptic Technology, Inc.
# Brian Heaney
import os
import sys
import cv2 as cv
import numpy as np
from functools import partial

class Rect:
    x = y = w = h = 0
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h 

if __name__ == "__main__":
    roiFile = "../Scans/PreTreat_SagittalScroll-1.png"
    newFile = "../Scans/PreTreat_SagittalScroll-2.png"
    if len(sys.argv) > 2: 
        roiFile = sys.argv[1]
        newFile = sys.argv[2]

    if not os.path.isfile(roiFile):
        print(f"Error: {roiFile} not found")
        exit()
    if not os.path.isfile(newFile):
        print(f"Error: {newFile} not found")
        exit()

    # Extract the human-determined ROI (prostate) from full ROI U/S frame
    roiRect = Rect(439, 226, 182, 195)
    #x, y, w, h = 439, 226, 182, 195
    roiFrame     = cv.imread(roiFile, cv.IMREAD_COLOR)
    roiGrayFrame = cv.cvtColor(roiFrame, cv.COLOR_BGR2GRAY)
    roiImage     = roiGrayFrame[roiRect.y:roiRect.y+roiRect.h, roiRect.x:roiRect.x+roiRect.w]
    cv.imshow("Prostate in frame 1", roiImage)

    # Draw a red rect around the ROI in the full u/s frame
    annotatedFrame = roiFrame.copy()
    annotatedFrame = cv.rectangle(annotatedFrame, (roiRect.x, roiRect.y), 
                                (roiRect.x + roiRect.w, roiRect.y + roiRect.h), 
                                (0, 0, 255), 1) 
  

    # extract the transverse and sagittal scans
    # x, y, w, h = 198, 91, 795, 453  
    # transverseImage = roiGrayFrame[y:y+h, x:x+w]
    #cv.imshow('Transverse', transverseImage) 
    # annotatedFrame = cv.rectangle(annotatedFrame, (x, y), 
    #                             (x + w, y + h), 
    #                             (255, 0, 0), 2) 


    # x, y, w, h = 198, y+h, 795, 464 
    # sagittalImage = roiGrayFrame[y:y+h, x:x+w]
    #cv.imshow('Sagittal', sagittalImage) 
    # annotatedFrame = cv.rectangle(annotatedFrame, (x, y), 
    #                             (x + w, y + h), 
    #                             (255, 255, 0), 2) 

    # find the ROI in the current frame



    while True:
        cv.imshow('Frame', annotatedFrame) # Display the full ultrasound image
        if cv.waitKey(25) & 0xFF == ord('q'):
            cv.destroyAllWindows()
            exit()
    # detectCircles = DetectCircles()
            
    # cv.namedWindow(detectCircles.processedImageWindowTitle)
    # cv.createTrackbar("Blur" , detectCircles.processedImageWindowTitle,  1, 20, detectCircles.setBlur )
    # cv.createTrackbar("Alpha", detectCircles.processedImageWindowTitle, 28, 50, detectCircles.setAlpha)
    # cv.createTrackbar("Beta" , detectCircles.processedImageWindowTitle, 49, 60, detectCircles.setBeta )
    # cv.createTrackbar("Thresh" , detectCircles.processedImageWindowTitle, 150, 200, detectCircles.setThresh)
    # cv.createTrackbar("Maxval" , detectCircles.processedImageWindowTitle, 200, 255, detectCircles.setMaxval)

    # if filename.find('.avi') > 0:
    #     video = cv.VideoCapture(filename)
    #     if not video.isOpened():
    #         print("empty video, exiting...")
    #         exit(-1)

    #     while True:
    #         ret, ultrasoundFrame = video.read() # Read a frame

    #         if not ret: # If frame is not read correctly, stream has ended
    #             print("Can't receive frame (stream end?). Restarting video...")
    #             video.set(cv.CAP_PROP_POS_FRAMES, 0)
    #             ret, ultrasoundFrame = video.read() # Read a frame
            
    #         grayImage = cv.cvtColor(ultrasoundFrame, cv.COLOR_BGR2GRAY)
    #         # get and display the transverse scan
    #         x, y, w, h = 198, 91, 795, 453  
    #         transverseImage = grayImage[y:y+h, x:x+w]
    #         cv.imshow('Transverse', transverseImage) 
    #         # ultrasoundImage = cv.rectangle(ultrasoundImage, (x, y), 
    #         #                             (x + w, y + h), 
    #         #                             (255, 0, 0), 2) 

    #         # get and display the sagittal scan
    #         x, y, w, h = 198, y+h, 795, 464 
    #         sagittalImage = grayImage[y:y+h, x:x+w]
    #         cv.imshow('Sagittal', sagittalImage) 
    #         # ultrasoundImage = cv.rectangle(ultrasoundImage, (x, y), 
    #         #                             (x + w, y + h), 
    #         #                             (255, 255, 0), 2) 

    #         cv.imshow('Video', grayImage) # Display the full ultrasound image

    #         # Process the sagittal image, drawing circles around any found circles
    #         detectCircles.processImage(sagittalImage)

    #         # Wait for a key press for a short duration (e.g., 25ms)
    #         # Press 'q' to quit
    #         if cv.waitKey(25) & 0xFF == ord('q'):
    #             exit()

    # exit(0)
 
