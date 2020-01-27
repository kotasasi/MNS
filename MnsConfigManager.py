#!/usr/bin/env python3
#Author: johan.austrin@volvocars.com
#Version: 2.0


import sys
import json
import urllib3.request
import base64
import os
import platform
import configparser
import time
from datetime import datetime
import traceback


""" ConfigManager
  Class designed to get and hold the device configuration retrieved from the central-config server.
  Also has function to get a local "back-up" configuration from the file system in case the config server fails to respond.  
"""
class ConfigManager:
  
  """ Constructor, sets various object parameters    
  Parameters:
    deviceId (str): The device Id o fthe unit, examples: MNS-EU-STAT-1, MNS-US-CAR-1 etc.      
  """
  
  def __init__(self, deviceId):
      self.device_id = deviceId
      
      self.configServer = None
      self.username = None
      self.password = None
      self.encoding = 'utf-8'

      self.endPoint = None
      self.additional_info = None
      self.gps_support = None
      self.pingServer = None
      self.pingEchos = None
      self.iperfServer = None
      self.iperfProtocol = None
      self.home = None

      #Different layout of HOME folder depending on OS
      if platform.system() == "Linux":
        if os.path.isdir("/home/ec2-user/mns/"):
          self.home = "/home/ec2-user/mns/"
        else:
          self.home = "/home/pi/mns/"
      elif platform.system() == "Windows":
        self.home = "C:\\MNS\\"

  """ Get device configuration
  Tries to call the configServer to get the device configuration. 
  If successful, the server parameters will be used by the object.
  If unsuccessful (i.e. server does not return a http 200 response or <timeout> ) the device will instead
  read the local config file (mns-config.ini) and use the local parameters instead.
  """
  def getServerConfig(self):
    print("About the GET device configuration from " + self.configServer)
    #GET from url (No retries)
    http = urllib3.PoolManager(retries=False)
    try:
      req = http.request(
        'GET',
        self.configServer,
        body=None,
        timeout=5.0,
        headers={
          'Authorization': 'Basic %s' % self.getBasicAuth(),
          'Content-Type': 'application/json; charset=utf-8'})
      #Evaluate the response
      httpResponse = str(req.status)
      #If successful response
      if (httpResponse=="200"):
        print("Got device config from server")
        jsonResponse = json.loads(req.data.decode(self.encoding))
        #Set object parameters to the ones returned from the server 
        self.endPoint = jsonResponse["reportEndpoint"]
        self.additional_info = jsonResponse["reportAdditionalInfo"]
        self.gps_support = jsonResponse["reportHasGps"]
        self.pingServer = jsonResponse["pingServer"]
        self.pingEchos = jsonResponse["pingEchos"]
        self.iperfServer = jsonResponse["iperfServer"] 
        self.iperfProtocol = jsonResponse["iperfProtocol"]
      else:
        print("Got HTTP error code: "+httpResponse)
        print("Will use local config instead")
        self.getLocalConfig()
    except urllib3.exceptions.ConnectTimeoutError:
      print("********************")
      print("Got ConnectTimeout when trying to connect to config-server. Please check internet connection!")
      print(str(traceback.format_exc()))
      print("********************")
      print("Will use local config instead")
      self.getLocalConfig()
    except:
      print("Got unforseen error when trying to connect to config-server")
      print(str(traceback.format_exc()))
      print("Will use local config instead")
      self.getLocalConfig()
    

  """ Read local config
  Reads the local configuration file to get server address and credentials (only).
  The idea is to use these parameters to get the server config.
  """
  def readLocalConfig(self, homeFolder):
    #Read GENERAL config values      
    self.config = configparser.ConfigParser() 
    self.config.read(homeFolder + "mns-config.ini")
    self.configServer = self.config['GENERAL']['ConfigServer'] + self.device_id 
    self.username = self.config['GENERAL']['username']
    self.password = self.config['GENERAL']['password']

  """Get local config
  If the server configuration can't be fetched, this method will be called to read the
  fall-back parameters stored in the local configuration file. 
  """
  def getLocalConfig(self):
    self.endPoint = self.config['GENERAL']['ReportEndPoint']
    self.additional_info = self.config['GENERAL']['AdditionalInfo']
    self.gps_support = self.config.getboolean('GENERAL', 'GpsSupport')
    self.pingEchos = self.config['PING']['echos']
    self.pingServer = self.config['PING']['DefaultPingServer']
    self.iperfServer = self.config['IPERF']['IperfServer']
    self.iperfProtocol = self.config['IPERF']['IperfMode']

  """ Get Basic Auth
  Support method to base64 encode the username and password used in the
  API request to the config-server
  """
  def getBasicAuth(self):
    #Basic Auth
    data = self.username + ":" + self.password    
    b64Val = base64.b64encode(bytes(data, self.encoding))
    return str(b64Val)[2:][:-1]


      
