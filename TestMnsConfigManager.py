import unittest
from MnsConfigManager import ConfigManager

class TestMnsConfigManager(unittest.TestCase):
    def test_init(self):
      testDeviceId = "MyTestDeviceId"
      testEncoding = "utf-8"
      testObject = ConfigManager(testDeviceId)
      #Assert values
      self.assertEqual(testObject.device_id, testDeviceId, "Assert testDeviceId is set")
      self.assertEqual(testObject.encoding, testEncoding, "Assert default encoding to be utf-8")
      #Assert None
      self.assertIsNone(testObject.configServer, "Assert default to be None")
      self.assertIsNone(testObject.username, "Assert default to be None")
      self.assertIsNone(testObject.password, "Assert default to be None")
      self.assertIsNone(testObject.endPoint, "Assert default to be None")
      self.assertIsNone(testObject.additional_info, "Assert default to be None")
      self.assertIsNone(testObject.gps_support, "Assert default to be None")
      self.assertIsNone(testObject.pingServer, "Assert default to be None")
      self.assertIsNone(testObject.pingEchos, "Assert default to be None")
      self.assertIsNone(testObject.iperfServer, "Assert default to be None")
      self.assertIsNone(testObject.iperfProtocol, "Assert default to be None")    
      #self.assertIsNone(testObject.home, "Assert default to be None")
    
    def test_readLocalConfig(self):
      testDeviceId = "MyTestDeviceId"
      testEncoding = "utf-8"
      testObject = ConfigManager(testDeviceId)
      testObject.readLocalConfig("")
      #List the expected values
      expected_configServer = "https://mns-log.c3.volvocars.com/config/?device_id="+testDeviceId
      expected_username = "reporter"
      expected_password = "Dc8IJ2CIzEDYKYyF"
      #Assert the received values 
      self.assertEqual(testObject.configServer, expected_configServer, "Assert expected Config server")
      self.assertEqual(testObject.username, expected_username, "Assert expected user name")
      self.assertEqual(testObject.password, expected_password, "Assert expected password")
      
    def test_getServerConfig(self):
      #This device exists on the server but will not be used/changed
      testDeviceId = "GOT5CG727382G"
      testEncoding = "utf-8"
      
      testObject = ConfigManager(testDeviceId)
      testObject.readLocalConfig("")
      testObject.getServerConfig()      
      #List the expected values
      expected_endPoint = "https://mns-log.c3.volvocars.com/result/"
      expected_additional_info = "@TESTING"
      expected_gps_support = False
      expected_pingServer = "8.8.8.8"
      expected_pingEchos = 5
      expected_iperfServer = "3.120.169.210"
      expected_iperfProtocol = "tcp"      
      #Assert the received values 
      self.assertEqual(testObject.endPoint, expected_endPoint, "Assert expected endPoint")
      self.assertEqual(testObject.additional_info, expected_additional_info, "Assert expected additional info")
      self.assertEqual(testObject.gps_support, expected_gps_support, "Assert expected gps_support")
      self.assertEqual(testObject.pingServer, expected_pingServer, "Assert expected ping server")
      self.assertEqual(testObject.pingEchos, expected_pingEchos, "Assert expected ping echos")
      self.assertEqual(testObject.iperfServer, expected_iperfServer, "Assert expected iperf server")
      self.assertEqual(testObject.iperfProtocol, expected_iperfProtocol, "Assert expected iperf protocol")

if __name__ == '__main__':
    unittest.main() 
      
      