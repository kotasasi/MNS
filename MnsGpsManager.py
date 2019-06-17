#!/usr/bin/env python3
#Author: johan.austrin@volvocars.com
#Version: 2.0

import gpsd
import time

class MnsGpsManager: 

  def __init__(self):
    #Defaults
    self.gps_lat = None
    self.gps_long = None
    self.initTime = 1
    self.backoffTime = 10
    self.attempts = 5

    self.connect()

  def connect(self):
    #print("Will try to get a GPS position...")
    i=0
    connected = False
    #We might have to try this a few times before we get a fixed position
    while (i<self.attempts):
      try:        
        #Connect to GPS using gpsd
        gpsd.connect()
        #Give the GPS some time to initialize
        time.sleep(self.initTime)
        #Read position (will return NoFixError if it fails)
        packet = gpsd.get_current()
        position = packet.position()
        #Got position, break
        self.gps_lat = position[0]
        self.gps_long = position[1]
        connected = True
        break
      except gpsd.NoFixError:
        #At boot-up it will take some extra time for the GPS to get fixed position
        i +=1
        print("Got NoFixError from GPS, will backoff for "+self.attempts + "s and try "
              + str(self.attempts-i) + " more attempts")
        #Wait for some time and try again
        time.sleep(self.backoffTime)
      except:
        i +=1
        print("Got Unknown error from gpsd. Will try again")
        time.sleep(self.backoffTime)
    if connected==False:
      print("Failed to get fixed GPS position after " +  str(self.attempts) + " attempts (Sorry)")
    if connected==True:
      print("Leaving MnsGpsManager with GPS location ("
            +str(self.gps_lat) + "," + str(self.gps_long) + ")")
