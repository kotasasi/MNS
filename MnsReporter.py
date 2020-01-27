#!/usr/bin/env python3
#Author: johan.austrin@volvocars.com
#Version: 2.0

import platform
from datetime import datetime
import os
import json
import urllib3.request
import glob
import subprocess
import traceback
""" MnsReporter
  Reporter class designed to independently report a test result to the central test result server
"""
class MnsReporter:

  """ Constructor
  """
  def  __init__(self, config):
    #Set constructor defaults
    self.device_id = platform.node()
    self.publicIpServer = "ifconfig.co/json"
    self.ipText = None
    self.privateIp = None
    self.privateIpInterface = "tun0"
    
    #Set default parameters
    self.encoding = 'utf-8'
    self.time = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    self.home = config.home
    self.unReportedPath = self.home + "results/unreported/"
     
    #Read local config values          
    config.readLocalConfig(config.home)
    #GET server config
    config.getServerConfig()
    #Get result folder
    self.createResultFolder()
    self.endPoint = config.endPoint
    self.basicAuth = config.getBasicAuth()   


  """ Get Public IP (address)
  Method used to get the Public IP address of the device. Calls the <publicIpServer> to get IP and Country
  and stores the result in the <publicIpServer> parameter.
  For more details, visit https://ifconfig.co/
  """
  def getPublicIp(self):
    print("About the GET public IP address from: " + self.publicIpServer)
    #GET to url
    http = urllib3.PoolManager()
    try:
      req = http.request(
        'GET',
        self.publicIpServer,
        body=None,
        timeout=5.0,
        headers={
          'Content-Type': 'application/json; charset=utf-8'})
      #Evaluate the response    
      httpResponse = str(req.status)
      if (httpResponse=="200"):
        jsonResponse = json.loads(req.data.decode(self.encoding))
        ip = str(jsonResponse["ip"])
        country = jsonResponse["country"]
        self.ipText = ip + " (" + country + ")"
        print("Public IP: " + self.ipText)        
      else:
        print("Public IP server returned error: " + httpResponse)        
    except:
      print("Failed to get Public IP. Please check Internet connection!")
  
  """ Get Private IP (address)
  Method to get the local IP of the device. In Linux (only), it creates a subprocess and calls ifconfig 
  to get the IP of the predefined interface <privateIpInterface>
  Currently not used in the response back to server but could be used if needed later on
  """
  def getPrivateIp(self):
    interface = self.privateIpInterface
    #Only Linux supported right now
    if (platform.system() == "Linux"):
      try:
        private_ip = subprocess.getoutput("/sbin/ifconfig %s" % interface).split("\n")[1].split()[1]
      except:
        private_ip = "Unknown"  
    
  """ Create Result Folder
  Method that creates a sub-folder to store the test results in if it doesn't already exist.
  The folder structure that will be created is as follows:
  <home> -> results -> <year> -> <month> -> <day>
  """  
  def createResultFolder(self):
    #Get current date(time)
    now = datetime.now()
    path = self.home + "results/" + str(now.year) + "/" + str(now.month) + "/" + str(now.day) + "/"
    #Check of folder exists
    if not os.path.isdir(path):    
      try:
        os.makedirs(path)
      except OSError:
        print ("Creation of the directory %s failed" % path)
        self.resultPath = self.home
      else:
        #print ("Successfully created the directory %s" % path)
        self.resultPath = path
    else:
      #print("path already exist: "+path)
      self.resultPath = path
    #print("Leaving createResultFolder with path: " + self.resultPath)

  """ Report from File
  
  Parameters: 
    filename (str): The full path to the file that holds the json result to report to server
  
  Method that reports a json formatted test-result and reports it to the central result server.
  If the report fails the method will move the <filename> to a separate folder to be reported later.  
  """
  #Report results to server
  def reportFromFile(self, filename):
    #Open file
    f = open(filename, "r")
    print("About to report the content in file: " + filename)
    #Get the payload from the file
    jsonLoad = json.load(f)
    #Add public IP to the operator string    
    jsonLoad["operator"] = self.ipText
    jsondata = json.dumps(jsonLoad)        
    # needs to be bytes
    jsondataasbytes = jsondata.encode(self.encoding)
    f.close()
    print("About to POST to URL: " + self.endPoint)
    print("Request body:\n" + jsondata)
    
    try:      
      #POST to url (no retires)
      http = urllib3.PoolManager(retries=False)
      #Build HTTP POST request
      req = http.request(
        'POST',
        self.endPoint,
        body=jsondataasbytes,
        timeout=5.0,
        headers={
          'Authorization': 'Basic %s' % self.basicAuth,
          'Content-Type': 'application/json; charset=utf-8',
          'Content-Length': len(jsondataasbytes)})    
      
      #Print the response    
      print("\n")
      print("Server http response: " + str(req.status))
      print("Response body:\n" + req.data.decode(self.encoding))      
    except urllib3.exceptions.ConnectTimeoutError:
      print("********************")
      print("Got ConnectTimeoutError in MnsReporter.reportFromFile()")
      print("********************")
      
      #Move filename to separate folder for re-reporting later
      self.movedFailed(filename)
    except:
      #Move filename to separate folder for re-reporting later
      print("Got unexpected error in MnsReporter.reportFromFile()")
      print(str(traceback.format_exc()))
      #self.movedFailed(filename)
  
  """ Move failed (file)
  
  Parameters: 
    filename (str): The full path of the file to be moved
    
  Moves the input filename to a separate folder to be re-reported later when the result server responds as expected.
  """
  def movedFailed(self, filename):
    #Actually, this will not move the file.
    #It will rather create a new file and remove the old one
    try:
      print("Report failed, will move test result to separate folder")
      oldFile = open(filename, "r")
      #Get the payload from the file (copy from working code)
      jsonLoad = json.load(oldFile)
      jsondata = json.dumps(jsonLoad)    
      jsondataasbytes = jsondata.encode(self.encoding)
      #Set destination folder
      
      #Set destination file name      
      newFileName = self.unReportedPath + filename.split("/")[-1]      
      #Write to file
      newFile = open(newFileName,"w")      
      newFile.write(jsondata)
      #Close and remove the old file
      newFile.close()
      oldFile.close()      
      os.remove(filename)
      print("Moved result file to unreported folder for further handling.")    
    except OSError as e:
      print(e)
    except:
      print("Unexpected error in movedFailed")
  
  """ Check for unreported results
  Checks to <unReportedPath> folder for any json files to report to the result server
  
  Returns: 
    True if there are any json-files in the <unReportedPath>
    False if there are NO json-files in the <unReportedPath>
  """
  def checkForUnreportedResults(self):
    #Get all josn-files in a list
    files = [f for f in glob.glob(self.unReportedPath + "**/*.json", recursive=True)]
    return files

  """ Report All unreported (files)
  Method will go through all the files in the <unReportedPath> folder and call the reportFromFile method 
  to report each result to the result server.  
  """
  def reportAllUnreported(self):    
    i=0
    for f in self.checkForUnreportedResults():
      try:
        #Try to report the result again
        self.reportFromFile(f)
        #Move the file to the report folder
        oldFile = open(f, "r")
        #Get the payload from the file (copy from working code)
        jsonLoad = json.load(oldFile)
        jsondata = json.dumps(jsonLoad)
        newFileName = self.resultPath + f.split("/")[-1]
        newFile = open(newFileName,"w")      
        newFile.write(jsondata)
        #Close and remove the old file
        newFile.close()
        oldFile.close()      
        os.remove(f)
        i=i+1
      except:
        print("Unexpected error in reportAllUnreported()")
    print("Done reporting the previously " + str(i) + " unreported results.")
    