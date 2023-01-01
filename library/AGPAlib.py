# Python library for automating polar alignment
# Designed to work with SkyX and Ken Sturrock's PySky
# Alex Gorbachev
# October, 2022

import serial.tools.list_ports
from witmotion import IMU
from cmath import pi
import geomag
from math import atan2, ceil
import time
from datetime import datetime
# Ken's main library
from .PySkyX_ks import *

max_move = 100

# GRBL command injection
def grbl_command(ser, command):
  command += "\r\n"
  #print ("Injecting " + command)
  ser.write(str.encode(command)) 
  time.sleep(2)
  while True:
    line = ser.readline()
    #print(line)
    if line == b'ok\r\n':
      time.sleep(2)
      return

def move_motors(port,direction, dist):
    #start_gcode = "G1G21G91"
    if dist > max_move:
        print ("Reducing distance to max units: " + str(max_move))
        dist = max_move
    elif dist <= 0:
        print ("Increasing distance to 1")
        dist = 1
    start_gcode = "G21G91"
    feed_rate = 1
    if direction == "left":
        cstr = f"{start_gcode}X{dist}Y-{dist}F{feed_rate}"
    elif direction == "right":
        cstr = f"{start_gcode}X-{dist}Y{dist}F{feed_rate}"
    elif direction == "up":
        cstr = f"{start_gcode}Z{dist}F{feed_rate}"
    elif direction == "down":
        cstr = f"{start_gcode}Z-{dist}F{feed_rate}"
    print("Moving " +  direction + " " + str(dist) + " units")
    grbl_command(port,cstr)

def move_motors_worm(port,direction, dist):
    #start_gcode = "G1G21G91"
    if dist > max_move:
        print ("Reducing distance to max units: " + str(max_move))
        dist = max_move
    elif dist <= 0:
        print ("Increasing distance to 1")
        dist = 1
    start_gcode = "G21G91"
    feed_rate = 1
    if direction == "right":
        cstr = f"{start_gcode}X-{dist}F{feed_rate}"
    elif direction == "left":
        cstr = f"{start_gcode}X{dist}F{feed_rate}"
    elif direction == "up":
        cstr = f"{start_gcode}Z{dist}F{feed_rate}"
    elif direction == "down":
        cstr = f"{start_gcode}Z-{dist}F{feed_rate}"
    print("Moving " +  direction + " " + str(dist) + " units")
    grbl_command(port,cstr)

def stopMotor(port):
    cstr = "M0"
    grbl_command(port,cstr)


def get_alt_align(port,lat,alt_bracket_offset):
    # Where are we on the vertical axis?
    imu = IMU(port)
    time.sleep(2)
    (x,y,z) = imu.get_angle()
    alt_align = round(lat - y - alt_bracket_offset,3)
    imu.close()
    return alt_align

def get_az_align(port,lat,lon,az_bracket_offset,mag_offset):
    # Where are we on the vertical axis?
    imu = IMU(port)
    time.sleep(2)
    (magRawX, magRawY, magRawZ) = imu.get_magnetic_vector()
    magdec = geomag.declination(lat,lon)
    heading = 180 * atan2(magRawY,magRawZ)/pi
    true_heading = heading + magdec
    calibrated_heading = round(true_heading - az_bracket_offset, 3)
    az_align = round(calibrated_heading - mag_offset,3)
    imu.close()
    return az_align

def find_serial_port(vid,pid):
    ports = serial.tools.list_ports.comports(include_links=False)
    for port in ports :
        # These are specific to my Arduino, can be found with dumping serial port data
        if port.vid == vid and port.pid == pid:
            time.sleep(1)
            return port.device
    print("Unable to locate device, Aborting.")
    exit()

def get_skyx_coords():
    TSXSend("sky6StarChart.DocumentProperty(0)")
    lat = float(TSXSend("sky6StarChart.DocPropOut"))
    TSXSend("sky6StarChart.DocumentProperty(1)")
    lon = float(TSXSend("sky6StarChart.DocPropOut"))
    return(lat,lon)
