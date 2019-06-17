#!/usr/bin/env python3
#Author: johan.austrin@volvocars.com
#Version: 2.0

import sys
import json
import urllib3.request
#import certifi
import base64
import os
import platform
import configparser
import gpsd
import time
from datetime import datetime

class ConfigManager:

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

  #GET device configuration
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
      if (httpResponse=="200"):
        print("Got device config from server")
        jsonResponse = json.loads(req.data.decode(self.encoding))
        
        self.endPoint = jsonResponse["reportEndpoint"]
        self.additional_info = jsonResponse["reportAdditionalInfo"]
        self.gps_support = jsonResponse["reportHasGps"]
        self.pingServer = jsonResponse["pingServer"]
        self.pingEchos = jsonResponse["pingEchos"]
        self.iperfServer = jsonResponse["iperfServer"]
        self.iperfProtocol = jsonResponse["iperfProtocol"]

        #If the additional_info specifies B2C we'd like to know the public ip
        """
        if ("@B2C" in self.additional_info):
          ip_fileName = "public_ip.txt"
          print("Using B2C, will check for public IP")
          command = "curl ifconfig.co/json > " + ip_fileName 
          print("Running command: " + command)
          os.system(command)
          #Open the file containing the test result
          file = open(ip_fileName, "r")
          result = file.readlines()
          result_json = json.dumps(result)
          print("Got response: " + str(result_json["ip"]))
          """
      else:
        print("Got HTTP error code: "+httpResponse)
        print("Will use local config instead")
        self.getLocalConfig()
    except urllib3.exceptions.ConnectTimeoutError:
      print("********************")
      print("Got ConnectTimeout when trying to connect to config-server. Please check internet connection!")
      print("********************")
      print("Will use local config instead")
      self.getLocalConfig()
    except:
      print("Got unforseen error when trying to connect to config-server")
      print("Will use local config instead")
      self.getLocalConfig()
    

  def readLocalConfig(self, homeFolder):
    #Read GENERAL config values      
    self.config = configparser.ConfigParser() 
    self.config.read(homeFolder + "mns-config.ini")
    self.configServer = self.config['GENERAL']['ConfigServer'] + self.device_id 
    self.username = self.config['GENERAL']['username']
    self.password = self.config['GENERAL']['password']

  def getLocalConfig(self):
    self.endPoint = self.config['GENERAL']['ReportEndPoint']
    self.additional_info = self.config['GENERAL']['AdditionalInfo']
    self.gps_support = self.config.getboolean('GENERAL', 'GpsSupport')
    self.pingEchos = self.config['PING']['echos']
    self.pingServer = self.config['PING']['DefaultPingServer']

  def getBasicAuth(self):
    #Basic Auth
    data = self.username + ":" + self.password    
    b64Val = base64.b64encode(bytes(data, self.encoding))
    return str(b64Val)[2:][:-1]


      
