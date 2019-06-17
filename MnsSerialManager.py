#!/usr/bin/env python3
#Author: johan.austrin@volvocars.com
#Version: 2.0

import serial

class MnsSerialManager:
  #Constructor
  def  __init__(self):
    port = "COM19"
    baudrate = 9600
    timeout = 2

    self.ser = serial.Serial(port,baudrate,timeout=0, parity=serial.PARITY_EVEN, rtscts=1)
    s = ser.read(100).decode("utf-8")
    
    
