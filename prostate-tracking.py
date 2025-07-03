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
    def copy(self):
        r = Rect(self.x, self.y, self.w, self.h)
        return r

if __name__ == "__main__":
    roiFile   = "../Scans/PreTreat_SagittalScroll-1.png"
    videoFile = "../Scans/PreTreat_SagittalScroll.avi"
    if len(sys.argv) > 2: 
        roiFile   = sys.argv[1]
        videoFile = sys.argv[2]

    if not os.path.isfile(roiFile):
        print(f"Error: {roiFile} not found")
        exit()
    if not os.path.isfile(videoFile):
        print(f"Error: {videoFile} not found")
        exit()

    # Extract the human-determined ROI (prostate) from full ROI U/S frame
    roiRect = Rect(434, 221, 192, 205)
    origRoiRect = roiRect.copy()
    #x, y, w, h = 439, 226, 182, 195
    roiFrame     = cv.imread  (roiFile , cv.IMREAD_COLOR)
    roiGrayFrame = cv.cvtColor(roiFrame, cv.COLOR_BGR2GRAY)
    roiImage     = roiGrayFrame[roiRect.y:roiRect.y+roiRect.h, roiRect.x:roiRect.x+roiRect.w]
    originalRoiImage = roiImage.copy()

    medianBlur = cv.medianBlur(roiImage, 5)   
    contrastImage = cv.convertScaleAbs(medianBlur, alpha=1.5, beta=0)
    ret,threshholdImage = cv.threshold(contrastImage,128,255,cv.THRESH_BINARY)
    cv.imshow("Threshold", threshholdImage)
    rows = roiImage.shape[0]
    # circles = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, 1, rows / 8,
    #                            param1=100, param2=30,
    #                            minRadius=0, maxRadius=0)
    circles = cv.HoughCircles(medianBlur, cv.HOUGH_GRADIENT, 1, rows / 8,
                               param1=100, param2=30,
                               minRadius=50, maxRadius=0)    
    if circles is not None:
        colorRoiImage = cv.cvtColor(roiImage, cv.COLOR_GRAY2BGR)
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            center = (i[0], i[1])
            # circle center
            cv.circle(colorRoiImage, center, 1, (0, 100, 255), 3)
            # circle outline
            radius = i[2]
            cv.circle(colorRoiImage, center, radius, (255, 0, 255), 3)
        cv.imshow("Circles in ROI" , colorRoiImage)

    # Draw a red rect around the ROI in the full u/s frame
    annotatedFrame = roiFrame.copy()
    annotatedFrame = cv.rectangle(annotatedFrame, (roiRect.x, roiRect.y), 
                                (roiRect.x + roiRect.w, roiRect.y + roiRect.h), 
                                (0, 0, 255), 1) 

    cv.imshow('ROI Frame', annotatedFrame) # Display the full ultrasound image

    video = cv.VideoCapture(videoFile)
    if not video.isOpened():
        print("empty video, exiting...")
        exit(-1)

    frameNumber = 1 
    while True:
        ret, newFrame = video.read() # Read a frame

        if not ret: # If frame is not read correctly, stream has ended
            print("Can't receive frame (stream end?). Restarting video...")
            video.set(cv.CAP_PROP_POS_FRAMES, 0)
            roiRect = origRoiRect.copy()
            roiImage = originalRoiImage.copy()
            frameNumber = 1
            ret, newFrame = video.read() # Read a frame

        newGrayFrame = cv.cvtColor(newFrame, cv.COLOR_BGR2GRAY)
    
        # find the ROI in the current frame by searching a 
        searchWindow = 20   # num pixels around the ROI rect to search for a match
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
        
        # write the frame # on the frame
        text = f"Frame {frameNumber}"
        org = (5, 560)  # Bottom-left corner of the text
        fontFace = cv.FONT_HERSHEY_SIMPLEX
        fontScale = 1.0
        color = (0, 255, 0)  # Green color in BGR
        thickness = 2
        lineType = cv.LINE_AA

        # Write the text on the image
        cv.putText(newAnnotatedFrame, text, org, fontFace, fontScale, color, thickness, lineType)
        frameNumber += 1

        roiRect.x = minX
        roiRect.y = minY
        roiImage = newImageRoi.copy()
        cv.imshow('new Frame', newAnnotatedFrame) # Display the full ultrasound image
        cv.imshow("Prostate in frame 1", roiImage)

        if cv.waitKey(25) & 0xFF == ord('q'):
            cv.destroyAllWindows()
            exit()
   
 
