from library.AGPAlib import *
from msvcrt import getch
import time

# Find the motor controller
GDEV = find_serial_port(6790,29987)
ser = serial.Serial(GDEV, 115200)

travel = int(input("Enter amount of travel: "))
print ("Press Esc to exit, arrows to control motors, t to change travel")

while True:
    key = ord(getch())
    if key == 27: #ESC
        break
    elif key == 116: #t
        travel = int(input("Enter amount of travel: "))
    elif key == 224: #Special keys (arrows, f keys, ins, del, etc.)
        key = ord(getch())
        if key == 80: #Down arrow
            print ("Down")
            move_motors_worm(ser,"down",travel)
        elif key == 72: #Up arrow
            print ("Up")
            move_motors_worm(ser,"up",travel)
        elif key == 75: #Up arrow
            print ("Left")
            move_motors_worm(ser,"left",travel)
        elif key == 77: #Up arrow
            print ("Right")
            move_motors_worm(ser,"right",travel)

ser.close()