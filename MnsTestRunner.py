#!/usr/bin/env python3
#Author: johan.austrin@volvocars.com
#Version: 2.0

import sys
import platform
from datetime import datetime

#MNS 2.0 specifics
from MnsConfigManager import ConfigManager
from MnsReporter import MnsReporter
from MnsPingTest import PingTest
from MnsIperf3Test import Iperf3Test

class MnsTestRunner:

  #Constructor
  def  __init__(self):
    #Set constructor defaults
    self.device_id = platform.node()
    self.time = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    self.config = ConfigManager(self.device_id)    
    self.testRun = None  
    
    #Create reporter
    self.reporter = MnsReporter(self.config)
    #print("Created Config- and Reporter")
    
#Main
def main():
  runner = MnsTestRunner()  
  argLength = len(sys.argv)
  args = sys.argv
  #print ('Number of arguments: ', argLength , 'arguments.')
  #print ('Argument List:', str(args))
  if argLength>0:
    mode = args[1]
    isDryRun=""
    if argLength >2:
        isDryRun=args[2]
    #Get the public IP address    
    runner.reporter.getPublicIp()
    iperfServers= runner.config.iperfServer.split(";")
    
    if mode == "bbk":
      print("BBK function called. Will run Brendbandskollen...Not")
      #result = testRun.runBbk()
    elif mode == "ping":
      print("Ping function called. Will run PingTest")
      testRun = PingTest(runner.config.additional_info, runner.config.gps_support)
      #Define filenames of the result files
      fileName = runner.reporter.resultPath + "ping_result_" + runner.time
      resultFile = fileName + ".txt"
      jsonFile = fileName + ".json"
      #Run the test and print it to resultFile
      testRun.run(runner.config.pingServer, runner.config.pingEchos, resultFile)
      #Evaluate the result
      testRun.evaluateResult(resultFile)
      #Format the result in json
      testRun.toJson(jsonFile)
      #Report to server
      # Report only if not Dryrun
      if isDryRun=="":
        runner.reporter.reportFromFile(jsonFile)
        #Report any unreported results to server
        runner.reporter.reportAllUnreported()
    elif mode == "iperf3":
      for iperfServer in iperfServers:
          print ("Running against iPerf server ......................" + iperfServer)
          print("IPERF3 function called. Will run IPERF3")
          testRun = Iperf3Test(runner.config.additional_info, runner.config.gps_support)
      #Define filenames of the result files
          fileName = runner.reporter.resultPath + "iperf3_result_" + iperfServer + "_" + runner.time
          resultFile = fileName + ".txt"
          jsonFile = fileName + ".json"
          #Run the test and print it to resultFile
          print (iperfServer)
          testRun.run(iperfServer, runner.config.iperfProtocol, resultFile)
          #Evaluate the result
          testRun.evaluateResult(resultFile)
          #Format the result in json
          testRun.toJson(jsonFile)
          #Report to server
          #Report only if not dryrun
          if isDryRun=="":
            runner.reporter.reportFromFile(jsonFile)
          #Report any unreported results to server
            runner.reporter.reportAllUnreported()
    elif mode == "config":      
      testRun.getServerConfig()
      result = False
    elif mode == "folders":
      testRun.createResultFolder()
      result = False
    elif mode == "report":
      testRun.repostResult(args[2], args[3])
    else:
      print("The function \'" + mode + "\' is not supported")
  else:
    print("You need to specify which function you want to execute.")
    print("Supported functions: bbk, ping, iperf3, config, folders")

if __name__ == "__main__":
  main()
