import sys
import platform
from datetime import datetime
import time
import os
import json
from MnsGpsManager import MnsGpsManager
import traceback
import urllib3.request
import requests
import re
import urllib.request

class BbkTest:
       
    def  __init__(self,additional_info, gps_support):
    #Set constructor defaults
        self.device_id = platform.node()
        self.gps_support = gps_support
        
        self.test_type = "BBK"    
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
    
        #Set default parameters
        self.encoding = 'utf-8'
        self.time = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        #Different layout depending on OS
        if platform.system() == "Linux":
          if os.path.isdir("/home/ec2-user/mns/"):
            self.home = "/home/ec2-user/mns/"
          else:
            self.home = "/home/pi/mns/"
        elif platform.system() == "Windows":
          self.home = "C://MNS//bbk//"
          

    def runBbk(self,filename):
        if (self.gps_support==True):
              gps = MnsGpsManager()
              self.gps_lat = gps.gps_lat
              self.gps_long = gps.gps_long
              self.country = gps.country
              self.gps_URL = gps.gps_URL
        self.mno,self.signalStrength=self.get_mno_and_signalstrength()
        self.filename = filename 
    #Different layout depending on OS    
        if platform.system() == "Windows":
          #command = "ECHO DryRun"
          command = self.home + "bbk_cli_win_amd64-1.exe > " + self.filename
        elif platform.system() == "Linux":      
          command = self.home + "bbk_cli > " + self.filename
        print("Running command: " + command)
        os.system(command)
        time.sleep(40)
        
    def evaluateResult(self,filename):
        self.filename=filename
        #Open the file containing the test result
        file = open(self.filename, "r")
        result = file.readlines()
        #Evaluate the BBK result
        self.test_type = "bbk"
        self.test_type_id = result[6].split(":")[-1].rstrip()    
        self.test_timestamp = datetime.utcnow().isoformat()    
        self.latency = result[3].split(":")[-1].lstrip().split(" ")[0].replace(",",".")
        self.download = result[4].split(":")[-1].lstrip().strip()
        self.upload = result[5].split(":")[-1].lstrip().rstrip()
        self.operator = result[1][18:].rstrip()
        print(self.download)
        
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
          'signalStrength': self.signalStrength,
          'operator': self.operator,
          'iperfServer': "N/A",
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