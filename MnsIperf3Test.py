#!/usr/bin/env python3
#Author: johan.austrin@volvocars.com
#Version: 2.0

import platform
import json
import subprocess
from datetime import datetime
from MnsGpsManager import MnsGpsManager
from MnsPingTest import PingTest

class Iperf3Test:        

  #Constructor
  def  __init__(self, additional_info, gps_support):
    #Set Test result defaults
    self.device_id = platform.node()
    self.gps_support = gps_support
    
    self.test_type = "Iperf3"    
    self.test_type_id = None
    self.test_timestamp = None
    self.gps_lat = None
    self.gps_long = None
    self.gps_URL = None
    self.latency = None
    self.download = None
    self.upload = None
    self.signalStrength = None
    self.operator = None
    self.additional_info = additional_info
    #iPerf3 specifics
    self.iperfProtocol = None
    self.jitter = None
    self.packetLoss = None
    self.iperf3TimeOut = 30
    self.errorPrefix = "iperf3: error - "
    #Results
    self.resultOriginal = None
    self.resultJson = None
    self.test_successfull = False
    self.iperfServer = None

  def run(self, iperfServer, iperfProtocol, filename):
    self.iperfServer = iperfServer
    #First, get GPS position if needed
    if (self.gps_support==True):
      gps = MnsGpsManager()
      self.gps_lat = gps.gps_lat
      self.gps_long = gps.gps_long
      self.gps_URL = gps.gps_URL
    errorText = ""
    #Set parameters
    self.test_timestamp = datetime.utcnow().isoformat()
    self.iperfProtocol= iperfProtocol
    #Add details on which iperfProtocol is used
    self.test_type_id = self.test_type + " for " + iperfProtocol + " (" + iperfServer + ")"
    #Different layout depending on OS
    if platform.system() == "Windows" :      
      path = "C:\MNS\iperf-3.1.3-win64\iperf3.exe"
      if (iperfProtocol == "udp"):
        command = path + " -u -c " + self.iperfServer + " > " + filename   
      else:
        command = path + " -c " + self.iperfServer + " > " + filename      
    elif platform.system() == "Linux":
      if (iperfProtocol == "udp"):
        print("Running iPerf3 for UDP packages on server " + self.iperfServer)
        command = "iperf3 -u -c " + self.iperfServer + " > " + filename
      else:
        print("Running iPerf3 for TCP packages on server " + self.iperfServer)
        command = "iperf3 -c " + self.iperfServer + " > " + filename        
    try:
      print("Running command (as sub-process): " + command)
      subprocess.run(args= command, shell=True, timeout=self.iperf3TimeOut)
      #As Iperf doesn't include latency we need to run a simple PingTest to get it
      #As we use a subprocess above this will be done in parallell
      self.runPing()
      #Done with Ping/Latency check                  
      self.test_successfull = True
    except subprocess.TimeoutExpired:
      self.test_successfull = False
      errorText = self.errorPrefix + "Command (" + command + ") reached max timeout (" + str(self.iperf3TimeOut) + "s)"
      self.errorToFile(errorText, filename)
      print(errorText)      
    except Exception:
      self.test_successfull = False
      errorText = self.errorPrefix + "Unknown error in subprocess.check_call"
      self.errorToFile(errorText, filename)      
      print(errorText)      

  def evaluateResult(self, filename):
    #Open the file containing the test result
    file = open(filename, "r")
    result = file.readlines()
    #Evaluate the IPERF3 result    
    if result[0].startswith(self.errorPrefix):
      #Iperf3 test failed with known error
      self.test_successfull = False
      #Fetch errorText
      errorText = result[0].split(" - ")[-1]
      #Add the errorText to the result
      self.test_type_id = errorText      
      self.additional_info= self.additional_info + " @ERROR: " + errorText      
    if ((self.iperfProtocol == "udp") and self.test_successfull):
      #print("Evaluating UDP result(s)")
      self.upload = result[-4].split("  ")[-4].split(" ")[0]
      self.jitter = result[-4].split("  ")[-3].split(" ")[0]
      self.packetLoss = result[-4].split("  ")[-2].split("(")[-1].split("%")[0]
      #Stuff the jitter and packetloss result in the signalStrength variable
      self.signalStrength = json.dumps(self.jitterResultInJson())
    elif ((self.iperfProtocol == "tcp") and self.test_successfull):
      #print("Evaluating TCP result(s)")
      self.download = result[-3].split("  ")[5].split("Mbits/sec")[0].rstrip()
      self.upload = result[-4].split("  ")[5].split("Mbits/sec")[0].rstrip()
    else:
      errorText = "Iperf3 test failed for unknown reason"
      print(errorText)
      self.additional_info= self.additional_info + " @ERROR: " + errorText
    print("IPerf3 result evaluated.")

  """ Result
  
  Returns:
    The result in JSON-format
  """
  def result(self):    
    return {      
      'device_id': self.device_id,
      'test_type': self.test_type,
      'test_type_id': self.test_type_id,
      'test_timestamp': self.test_timestamp,
      'gps_lat': self.gps_lat,
      'gps_long': self.gps_long,
      'gps_url': self.gps_URL,
      'latency': self.latency,
      'download': self.download,
      'upload': self.upload,
      'iperfServer': self.iperfServer,
      'signalStrength': self.signalStrength,
      'operator': self.operator,
      'additional_info': self.additional_info
      }

  """ Jitter result in json 
  
  Prints the jitter and packetloss result in JSON-format.
  Note: Jitter is only applicable for UDP data
  """
  def jitterResultInJson(self):
    #Add jitter & packetloss results as json 
    return {
      'jitter':self.jitter,
      'packetloss': self.packetLoss
      }

  """ toJson
  Parameters: 
    filename (str): The full path to the filename to save the json formatted text to
  
  Saves the payload to file
  """
  def toJson(self, filename):
    #Save payload to file
    jsondata = json.dumps(self.result())
    f = open(filename, "a")
    f.write(jsondata)
    f.close()

  #Print error to file
  def errorToFile(self, errorText, filename):
    #Save error text to file    
    f = open(filename,"a")
    f.write(errorText)
    f.close()
    
  def runPing(self):
    #As Iperf doesn't include latency we need to run a simple PingTest to set the latency
    pingResult = "tempPing.txt"
    pingTest = PingTest(self.additional_info, False)
    pingTest.run(self.iperfServer, 5, pingResult)
    pingTest.evaluateResult(pingResult)
    self.latency = pingTest.latency
