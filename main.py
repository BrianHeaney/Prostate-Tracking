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
    roiFrame     = cv.imread  (roiFile , cv.IMREAD_COLOR)
    roiGrayFrame = cv.cvtColor(roiFrame, cv.COLOR_BGR2GRAY)
    roiImage     = roiGrayFrame[roiRect.y:roiRect.y+roiRect.h, roiRect.x:roiRect.x+roiRect.w]
    cv.imshow("Prostate in frame 1", roiImage)

    newFrame     = cv.imread  (newFile , cv.IMREAD_COLOR)
    newGrayFrame = cv.cvtColor(newFrame, cv.COLOR_BGR2GRAY)

    # Draw a red rect around the ROI in the full u/s frame
    annotatedFrame = roiFrame.copy()
    annotatedFrame = cv.rectangle(annotatedFrame, (roiRect.x, roiRect.y), 
                                (roiRect.x + roiRect.w, roiRect.y + roiRect.h), 
                                (0, 0, 255), 1) 
  
    # find the ROI in the current frame by searching a 
    searchWindow = 3   # num pixels around the ROI rect to search for a match
    diffList = []
    index = minIndex = 0
    minErr = 0
    minX = minY = 0
    for x in range(roiRect.x - searchWindow, roiRect.x + searchWindow):
         for y in range(roiRect.y - searchWindow, roiRect.y + searchWindow):
            # extract the ROI rect from the new image, located at <x, y>
            newImage = newGrayFrame[y:y+roiRect.h, x:x+roiRect.w]
            diff = cv.subtract(roiImage, newImage)
            err = np.sum(diff**2)
            if index == 0 or err < minErr:
                minIndex = index
                minErr = err
                minX = x
                minY = y

            mse = err/(float(roiImage.size))
            diffList.append((index, x, y, err))
            index += 1

    # find the best match (least error) in the search window
    diff = diffList[minIndex]
    newImageRoi = newGrayFrame[minY:minY+roiRect.h, minX:minX+roiRect.w]
    newAnnotatedFrame = cv.rectangle(newFrame, (minX, minY), 
                                (minX + roiRect.w, minY + roiRect.h), 
                                (0, 255, 255), 1) 

    while True:
        cv.imshow('ROI Frame', annotatedFrame) # Display the full ultrasound image
        cv.imshow('new Frame', newAnnotatedFrame) # Display the full ultrasound image
        if cv.waitKey(25) & 0xFF == ord('q'):
            cv.destroyAllWindows()
            exit()
   
 
