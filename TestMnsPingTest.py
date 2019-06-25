import unittest
import json

from MnsPingTest import PingTest

class TestMnsPingTest(unittest.TestCase):
    """
    Test of default constructor
    """
    def test_init(self):        
      #Set the mandatory information
      add_info = "test_info"
      gps_sup = False
      #Create testObject with the values
      testObject = PingTest(add_info, gps_sup)
      #Assert default values
      self.assertIsNone(testObject.test_type_id, "Assert that value is None")
      self.assertIsNone(testObject.test_timestamp, "Assert that value is None")        
      self.assertIsNone(testObject.gps_lat,"Assert that value is None")
      self.assertIsNone(testObject.gps_long, "Assert that value is None")
      self.assertIsNone(testObject.latency, "Assert that value is None")
      self.assertIsNone(testObject.download, "Assert that value is None")
      self.assertIsNone(testObject.upload,"Assert that value is None")
      self.assertIsNone(testObject.signalStrength,"Assert that value is None")
      self.assertIsNone(testObject.operator,"Assert that value is None")
      self.assertIsNone(testObject.packetloss,"Assert that value is None")
      self.assertIsNone(testObject.minimum,"Assert that value is None")
      self.assertIsNone(testObject.maximum,"Assert that value is None")
      self.assertIsNone(testObject.average,"Assert that value is None")
      #Assert that the provided values have been set
      self.assertEqual(testObject.additional_info, add_info, "Assert that additional_info is set")
      self.assertEqual(testObject.gps_support, gps_sup, "Assert that GPS_support is False")
        
    def test_evaluateResult(self):
       #Set the mandatory information
        add_info = "test_info"
        gps_sup = False
        filename = "pingResultWin.txt"
        #Create testObject with the values
        testObject = PingTest(add_info, gps_sup)
        testObject.evaluateResult(filename)
        #Expected values
        expected_latency = "26"
        expected_minimum = "15"
        expected_maximum = "50"
        expected_average = "26"
        expected_packetloss = "0"
        #Assert values
        self.assertEqual(testObject.latency, expected_latency , "Assert latency value")
        self.assertEqual(testObject.minimum, expected_minimum , "Assert minimum value")
        self.assertEqual(testObject.maximum, expected_maximum , "Assert maximum value")
        self.assertEqual(testObject.average, expected_average , "Assert average value")
        self.assertEqual(testObject.packetLoss, expected_packetloss , "Assert packet loss value")
        
    def test_result(self):
      add_info = "test_info"
      gps_sup = False
      if (platform.system() == "Linux"):
        filename = "pingResultLinux.txt"
      if (platform.system() == "Windows"):
        filename = "pingResultWin.txt"
      #Create testObject with the values
      testObject = PingTest(add_info, gps_sup)
      testObject.evaluateResult(filename)
      testObject.result()
            
    
if __name__ == '__main__':
    unittest.main()
