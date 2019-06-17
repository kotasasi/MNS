#!/usr/bin/env python3
#Author: johan.austrin@volvocars.com
#Version: 2.0

import platform
import os
import json
from datetime import datetime
from MnsGpsManager import MnsGpsManager

class PingTest:        

  #Constructor
  def  __init__(self, additional_info, gps_support):
    #Set Test result defaults
    self.device_id = platform.node()
    self.gps_support = gps_support
    self.test_type = "Ping"
    self.pingServer = "8.8.8.8"
    self.pingEchos = 10
    self.test_type_id = None
    self.test_timestamp = None
    self.gps_lat = None
    self.gps_long = None
    self.latency = None
    self.download = None
    self.upload = None
    self.signalStrength = None
    self.operator = None
    self.additional_info = additional_info
    #Ping specifics
    self.packetloss = None
    self.minimum = None
    self.maximum = None
    self.average = None
    #Results
    self.resultOriginal = None
    self.resultJson = None
    self.pingResult = None

  def run(self, server, echos, filename):    
    if (self.gps_support==True):
      gps = MnsGpsManager()
      self.gps_lat = gps.gps_lat
      self.gps_long = gps.gps_long
    self.test_timestamp = datetime.utcnow().isoformat()
    #Different layout depending on OS
    if platform.system() == "Windows" :      
      command = "ping " + server + " -n " + str(echos) + " > " + filename      
    elif platform.system() == "Linux":
      command = "ping " + server + " -c " + str(echos) + " > " + filename
    print("Running command: " + command)
    os.system(command)

  def evaluateResult(self, filename):
    self.pingResult = "Undefined!"
    #Open the file containing the test result
    file = open(filename, "r")
    result = file.readlines()    
    #Evaluate the PING result
    if platform.system() == "Windows" :
      if(result[2] == "Request timed out.\n"):
        #Request timed out, check packet loss
        self.packetLoss = result[-1].split(",")[-2].split("(")[-1].split("%")[0].lstrip().rstrip()
        print("packetLoss: " + self.packetLoss)
        if (self.packetLoss == "100"):
          self.pingResult = " @ERROR, Request timed out: 100% packet loss"
          self.latency = 0
      else:
        self.packetLoss = result[-3].split(",")[-2].split("(")[-1].split("%")[0].lstrip().rstrip()
        self.latency = result[-1].split(",")[-1].split("=")[-1].split("ms")[0].lstrip().rstrip()      
        splitResult = result[-1].split(",")
        minimum = str(splitResult[0].split("=")[-1].split("ms")[0]).lstrip()
        maximum = str(splitResult[1].split("=")[-1].split("ms")[0]).lstrip()
        average = str(splitResult[2].split("=")[-1].split("ms")[0]).lstrip()
        self.pingResult = " min/avg/max = " + minimum + "/" + average + "/" + maximum + " ms"
    elif platform.system() == "Linux" :
      #First, check packetloss
      self.packetLoss = result[-2].split(",")[-2].split("%")[0].lstrip().rstrip()
      if(self.packetLoss == "100"):        
        self.pingResult = " @ERROR, Request timed out: 100% packet loss"
        self.latency = 0
      else:
        self.latency = latency = result[-1].split("=")[-1].split("/")[1].rstrip()      
        self.pingResult = result[-1].split("rtt")[-1].lstrip().rstrip()
    print("pingResult: " + self.pingResult)
    self.additional_info += self.pingResult

   #Print the result in JSON-format
  def result(self):    
    return {      
      'device_id': self.device_id,
      'test_type': self.test_type,
      'test_type_id': self.test_type_id,
      'test_timestamp': self.test_timestamp,
      'gps_lat': self.gps_lat,
      'gps_long': self.gps_long,
      'latency': self.latency,
      'download': self.download,
      'upload': self.upload,
      'signalStrength': self.signalStrength,
      'operator': self.operator,
      'additional_info': self.additional_info
      }

  def toJson(self, filename):
    #Save payload to file
    jsondata = json.dumps(self.result())
    f = open(filename, "x")
    f.write(jsondata)
    f.close()
    
    
