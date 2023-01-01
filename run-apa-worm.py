#!/usr/bin/env python3
####################
# Import Libraries #
####################

from library.PySkyX_ks import *
from library.AGPAlib import *

import time
import os

import math
import cv2
from astropy.io import fits

import serial.tools.list_ports
import serial

# Exposure
exposure = 2
# Gaussian blur radius
radius = 33
# Acceptable distance to origin to end run
ok_dist_to_origin = 100
# Acceptable distance to tangent point to move to next axis
ok_dist_to_tangent = 100
# Number of iterations to end the program
max_iterations = 90
# max motor move units
max_move = 10
# Backlash detection, if moved less than this number of pixels
backlash_pix_move = 30
# Motion initial moves and hints
travel = {}
expected_resolution = {}
travel["vertical"] = 8
travel["horizontal"] = 10
# These are system specific, and need to be measured
expected_resolution["vertical"] = 51
expected_resolution["horizontal"] = 74

def swap_direction(axis):
    if axis == "vertical":
        direction[axis] = "up" if (direction[axis] == "down") else "down"
    else:
        direction[axis] = "left" if (direction[axis] == "right") else "right"
    print ("Reversing direction to: " + direction[axis])


def take_image():
    TSXSend("ccdsoftCamera.filterWheelConnect()")	
    TSXSend("ccdsoftCamera.FilterIndexZeroBased = 0") # Luminance    
    timeStamp("Taking image: " + str(exposure) + "s")
    TSXSend("ccdsoftCamera.Asynchronous = false")
    TSXSend("ccdsoftCamera.AutoSaveOn = true")
    TSXSend("ccdsoftCamera.Frame = 1")
    TSXSend("ccdsoftCamera.Subframe = false")
    TSXSend("ccdsoftCamera.ExposureTime = " + str(exposure))
    TSXSend("ccdsoftCamera.Delay = 1")
    TSXSend("ccdsoftCamera.TakeImage()") 
    TSXSend("ccdsoftCameraImage.AttachToActiveImager()")
    cameraImagePath =  TSXSend("ccdsoftCameraImage.Path").split("/")[-1] 
    return cameraImagePath

# Find the motor controller
GDEV = find_serial_port(6790,29987)
ser = serial.Serial(GDEV, 115200)

# Set the desired autosave directory
ASPath = "C:/Users/Alex/Pictures/cal/apa"
# Make this dir or ignore if it already exists
os.makedirs(ASPath, exist_ok=True)
# Set the autopath root, TSX will append a date folder to it
TSXSend("ccdsoftCamera.AutoSavePath = '" + ASPath + "'")

starcoords = []
ctrdists = []
resolution = {}
direction = {}
backlash = {}

while True:
    # Start with horizontal b/c vertical me be perfect due to angle sensor
    for axis in ("horizontal","vertical"):
        axis_runs = 0
        while True:
            imgfile = take_image()
            imgData = fits.getdata(imgfile, ext=0)
            os.remove(imgfile) # clean up
            (imgY,imgX) = (imgData.shape) # size of image in pixels
            
            # find the (x, y) coordinates of the area of the image with the largest intensity value
            imgData = cv2.GaussianBlur(imgData,(radius,radius), 0)
            (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(imgData)

            #print ("min " + str(minVal) + " max " + str(maxVal) + " minloc " + str(minLoc) + " maxloc " + str(maxLoc))

            # Coordinates of the star
            (starX, starY) = maxLoc
            starcoords.append(maxLoc)
            iteration = len(starcoords)
            iter_index = iteration - 1
            print("\r\nIteration: " + str(iteration))

            # Coordinates of center (crosshairs) of image
            midX = int(imgX/2)
            midY = int(imgY/2)

            print (f"Star at {starX},{starY} - Center at {midX},{midY}")

            # Calculate the Euclidean distance to origin
            DistToOrig = int(math.dist([starX, starY], [midX, midY]))
            ctrdists.append(DistToOrig)
            print("Distance to center: " + str(DistToOrig))

            # Are we close enough to finish up?
            if DistToOrig <= ok_dist_to_origin:
                print("We are close enough, exiting.")
                ser.close()
                exit()

                # Have we reach maximum iterations
            if iteration > max_iterations:
                print("Reached maximum moves, exiting.")
                ser.close()
                exit()

            # Ask if we want to proceed or exit
            #abortYN = input("Abort further tries? (YN): ").upper()
            #if abortYN == "Y":
            #    ser.close()
            #    exit()

            # take a guess as to direction
            if axis_runs == 0 and iteration == 1:
                direction["horizontal"] = "right" if starX < midX else "left"
                direction["vertical"] = "up" if starY < midY else "down"

            # Run analysis when we have at least 2 points of the line
            if axis_runs > 1:
                pix_traveled = int(math.dist(starcoords[iter_index], starcoords[iter_index - 1]))
                resolution[axis] = pix_traveled/travel[axis]
                # Sanity check for after backlash travel
                if resolution[axis] < (expected_resolution[axis] / 2):
                    resolution[axis] = expected_resolution[axis]

                # We traveled too little, ignore for small moves
                if pix_traveled < backlash_pix_move and travel[axis] > 7:
                    backlash_travel = int(travel[axis] - pix_traveled / resolution[axis])
                    print (f"Moved only {pix_traveled} pixels, possible backlash,compensating {backlash_travel} units")
                    move_motors_worm(ser,direction[axis],backlash_travel)
                    continue

                print (f"Traveled {direction[axis]} for {pix_traveled} pixels at {resolution[axis]} pixels/unit")

                # Where is the tangent point with the middle?
                (X1, Y1) = starcoords[iter_index]
                (X2, Y2) = starcoords[iter_index - 1]
                X3 = midX
                Y3 = midY

                # Coordinates of the tangent intersect point
                if axis_runs == 2 or travel[axis] > 5:
                    # per http://paulbourke.net/geometry/pointlineplane/
                    p2p1 = math.dist([X1, Y1], [X2, Y2])
                    u = ((X3-X1)*(X2-X1) + (Y3-Y1)*(Y2-Y1)) / (p2p1 * p2p1)
                    X = int(X1 + u*(X2-X1))
                    Y = int(Y1 + u*(Y2-Y1))

                pixels_to_tangent = int(math.dist([X1, Y1], [X, Y]))
                print (f"Tangent point X={X} Y={Y} distance from current position: {pixels_to_tangent}")
                
                # Set new distance to travel so we reach the tangent point
                # Undershoot a little, because reversing reduces precision
                travel[axis] = int(pixels_to_tangent * 0.95 / resolution[axis])
                if travel[axis] == 0:
                    print ("Increasing distance from 0 to 3")
                    travel[axis] = 3
                elif travel[axis] > max_move:
                    print (f"Reducing distance from {travel[axis]} to max {max_move} units")
                    travel[axis] = max_move

                if pixels_to_tangent <= ok_dist_to_tangent:
                    print(f"Close enough to tangent, ending this {axis} axis run")
                    break
               
                # Have we overshot the tangent?
                (XP, YP) = starcoords[iter_index -1]
                prev_pix_to_tangent = int(math.dist([XP, YP], [X, Y]))

                # Reverse either if we overshot tangent, or getting away from center
                if (pix_traveled > prev_pix_to_tangent) or (ctrdists[iter_index] > ctrdists[iter_index-1]):
                    swap_direction(axis)
                                        
            # Move
            move_motors_worm(ser,direction[axis],travel[axis])

            # Increment per axis counter
            axis_runs += 1
