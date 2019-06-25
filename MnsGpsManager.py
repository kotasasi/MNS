#!/usr/bin/env python3
#Author: johan.austrin@volvocars.com
#Version: 2.0

#pip3 install gpsd-py3
#https://github.com/MartijnBraam/gpsd-py3
import gpsd
import time

class MnsGpsManager: 


  """ Constructor, sets the local variables
  """
  def __init__(self):
    #Defaults
    self.gps_lat = None
    self.gps_long = None
    self.gps_URL = None
    self.initTime = 1
    self.backoffTime = 10
    self.attempts = 5

    self.connect()


  """ Connect
  Using the GPSD library this method tries to connect to the GPS shield to get the GPS position.
  As the GPS signal might not be fixed at first attempt this method will try for a number of <attempts>. 
  If the attempt fails, it will back-off for <backoffTime> seconds and try again. If it fails after max <attempts> 
  the position will be set to None.
  
  Sets parameters:
    gps_lat (long): the current GPS Lat position, example 57.70716
    gps_long (long): the current GPS Long position, example 11.96679
    gps_URL (string): the current GPS position formatted as a OpenMap URL, example: 
      https://www.openstreetmap.org/?mlat=57.72592&mlon=11.850768333&zoom=15
  """
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
        self.gps_URL = packet.map_url()
        connected = True
        break
      except gpsd.NoFixError:
        #At boot-up it will take some extra time for the GPS to get fixed position
        i +=1
        print("Got NoFixError from GPS, will back-off for "+self.attempts + "s and try "
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
