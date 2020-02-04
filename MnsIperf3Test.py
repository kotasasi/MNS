#!/usr/bin/env python3
#Author: johan.austrin@volvocars.com
#Version: 2.0

import platform
import json
import subprocess
import traceback
import urllib3.request
import requests
import re
import urllib.request
from datetime import datetime
import time
from MnsGpsManager import MnsGpsManager
from MnsPingTest import PingTest




def get_ip_port(_str):
    ip = _str.split(':')[0]
    try:
        port = _str.split(':')[1]
    except:
        port = '5201'
    return ip, port

def restart_iperf_server(iPerfServer,iperfPort):
  print("Starting iPerf server before the test")  
  http = urllib3.PoolManager(retries=False)
  path = 'http://' + iPerfServer + ':5210' + '/restart_iperf3/' + str(iperfPort)
  print(path)
  try:
    print("Trying to restart iPerf")
    req = http.request('GET', path, body=None, timeout=5.0)
    #Evaluate the response
    httpResponse = str(req.status)
    print(httpResponse)
    if httpResponse=="200":
      print("iPerf server restarted")
  except urllib3.exceptions.ConnectTimeoutError:
    print("********************")
    print("Got ConnectTimeout when trying to connect to AWS. Please check internet connection!")  



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
    self.country = None
    self.mno = None
    self.mccmnc=None
    self.signalValue=None
    self.latency = None
    self.download = None
    self.upload = None
    self.signalStrength = None
    self.connectionState = None
    self.technology = None
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
    self.iperfPort= None
    self.device=None

  def run(self, iperfServer, iperfProtocol, filename,device):
    
    ip, port = get_ip_port(iperfServer)
    self.iperfServer = ip
    self.iperfPort = port
    self.device=device
    #First, get GPS position if needed
    if (self.gps_support==True):
      gps = MnsGpsManager()
      self.gps_lat = gps.gps_lat
      self.gps_long = gps.gps_long
      self.country = gps.country
      self.gps_URL = gps.gps_URL
    self.mno,self.signalStrength=self.get_mno_and_signalstrength()
    #self.connectionState, self.technology =  self.get_connection_and_technology()
    print(self.mno)
    print(self.signalStrength)
    errorText = ""
    #Set parameters
    self.test_timestamp = datetime.utcnow().isoformat()
    self.iperfProtocol= iperfProtocol
    #Add details on which iperfProtocol is used
    self.test_type_id = self.test_type + " for " + iperfProtocol + " (" + iperfServer + ")"
    #Restart iPerf Server and wait
    restart_iperf_server(self.iperfServer,self.iperfPort)
    time.sleep(5)
    #Different layout depending on OS
    if (platform.system() == "Windows" and self.device=="windows"):      
      path = "C:\MNS\iperf-3.1.3-win64\iperf3.exe"
      if (iperfProtocol == "udp"):
        command = path + " -u -c " + self.iperfServer + " -p " + str(self.iperfPort)+ " > " + filename  
      else:
        command = path + " -c " + self.iperfServer + " -p " + str(self.iperfPort)+  " > " + filename
        print(command)      
    elif (platform.system() == "Linux" and self.device == "pi"):
      if (iperfProtocol == "udp"):
        print("Running iPerf3 for UDP packages on server " + self.iperfServer)
        command = "iperf3 -u -c " + self.iperfServer + " > " + filename
      else:
        print("Running iPerf3 for TCP packages on server " + self.iperfServer)
        command = "iperf3 -c " + self.iperfServer + " -p " + str(self.iperfPort) + " > " + filename                
    elif (platform.system() == "Linux" and (self.device == "tcam" or self.device == "ihu")):
        print("Running iPerf3 for TCP packages on server " + self.iperfServer)
        command = " adb shell /data/iperf3 -c " + self.iperfServer + " -p " + str(self.iperfPort) + " > " + filename        
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
      errorText = self.errorPrefix + "Unknown error in subprocess.check_call: " + str(traceback.format_exc())
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
      #self.test_type_id = errorText      
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
      'country': self.country,
      'mno': self.mno,
      'mccmnc': self.mccmnc,
      'connectionstate': self.connectionState,
      'technology': self.technology,
      "rssisignal" : self.signalValue,
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
    ip, port = get_ip_port(self.iperfServer)
    self.iperfServer = ip
    self.iperfPort = port
    pingResult = "tempPing.txt"
    pingTest = PingTest(self.additional_info, False)
    pingTest.run(self.iperfServer, self.iperfPort, 5, pingResult)
    pingTest.evaluateResult(pingResult)
    self.latency = pingTest.latency
  
  def get_mno_and_signalstrength(self):
    try:
        signalStrength=""
        response=requests.get("http://192.168.1.1/model.json",auth=('admin', 'volvo4life'))
        jsonResponse = json.loads(response.content.decode("utf-8"))
        #mno=str(jsonResponse["wwan"]["registerNetworkDisplay"])
        mcc=jsonResponse["wwanadv"]["MCC"]
        print(mcc)
        mnc=jsonResponse["wwanadv"]["MNC"]
        print(mnc)
        self.mccmnc=str(mcc)+","+str(mnc)
        mno=self.get_mno(mcc,mnc)                
        self.signalValue=jsonResponse["wwan"]["signalStrength"]["rssi"]
        print(self.signalValue)
        #if (signalValue > -10):
        #    signalStrength="Excellent"
        #elif (signalValue >= -15 and signalValue <= -10):
        #    signalStrength="Good"
        #elif (signalValue < -15):
        #    signalStrength="Poor"
        if (self.signalValue >= -70):
            signalStrength = "Excellent"
        elif (self.signalValue < -70 and self.signalValue >= -85):
            signalStrength = "Good"
        elif (self.signalValue < -85 and self.signalValue >= -100):
            signalStrength = "Fair"
        elif (self.signalValue < -100):
            signalStrength = "Poor"
        elif (self.signalValue < -110):
            signalStrength = "No Signal"
    except:
        print(traceback.format_exc())
        mno="null"
        signalStrength="null"
    return mno, signalStrength

  def get_mno(self,mcc,mnc):
    td_re = re.compile('<td>([^<]*)</td>'*6)
    url = "http://mcc-mnc.com/"
    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request)
    html = response.read().decode('utf-8')
    
    tbody_start = False

    mcc_mnc_list = []
    try:
        for line in html.split('\n'):
            if '<tbody>' in line:
                tbody_start = True
            elif '</tbody>' in line:
                break
            elif tbody_start:
                td_search = td_re.search(line)
                current_item = {}
                td_search = td_re.split(line)
                if (td_search[1] == mcc and td_search[2] == mnc):  
                    mno=td_search[6][0:-1]
                    return mno
    except:
        mno="null"
  def get_connection_and_technology(self):
     try:
        self.connectionState = jsonResponse["wwan"]["connection"]
        self.technology =  jsonResponse["wwan"]["currentPSserviceType"]
     except:
        self.connectionState = "null"   
        self.technology = "null"
