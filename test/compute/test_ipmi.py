# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
import unittest
from mock import Mock

from libcloud.compute.drivers.ipmi import IpmiNodeDriver
from libcloud.compute.base import Node
from test import LibcloudTestCase
import commands

class IpmiTests(LibcloudTestCase):

    ON, OFF, ERROR = range(3)

    def setUp(self):
        self.key = 'key'
        self.secret = 'secret'
        self.host = '127.0.0.1'
        self.port = 663
        self.driver = IpmiNodeDriver(self.key, self.secret, self.host, self.port)
        self.count = {"status":0, "on":0, "off":0, "soft":0, "reset":0}
        commands.getstatusoutput = Mock(side_effect = self.mock_ipmitool)
        self.mock_nodes = [Node(1,self.host,'on',self.host,'',self.driver), Node(1,self.host,'off',self.host,'',self.driver), Node(1,self.host,'unknown',self.host,'',self.driver)]
        self.iter = {}
        self.iter['status'] = [(0, "Chassis Power is on"), (0, "Chassis Power is off"), (1, "Error: Unable to establish LAN session\nUnable to get Chassis Power Status")]
        self.iter['on'] = [None, (0, "Chassis Power Control: On"), (1, "Operation cannot be performed: \nSOAP Fault:")]
        self.iter['off'] = [(0, "Chassis Power Control: Off"), None, (1, "Operation cannot be performed: \nSOAP Fault:")]
        self.iter['soft'] = [(0, "Chassis Power Control: Soft"), None, (1, "Operation cannot be performed: \nSOAP Fault:")]
        self.iter['reset'] = [(0, "Chassis Power Control: Reset"), None, (1, "Operation cannot be performed: \nSOAP Fault:")]

    def mock_ipmitool(self, str):
        if(str.startswith("ipmitool ")):
            command = str.replace("ipmitool -H %s -U %s -P %s " % (self.host, self.key, self.secret), "")
            command = command.replace("chassis power ", "")
            if(self.iter.has_key(command) and self.count.has_key(command)):
                return self.iter[command][self.count[command]]
            else:
                return (1, "No command provided!\n")
        else:
            return (1, "%s: command not found" % str)

    def test_list_nodes(self):
        # success
        self.count['status'] = self.ON
        mock_node = self.mock_nodes[self.ON]
        nodes = self.driver.list_nodes()
        self.assertTrue(isinstance(nodes, list))
        self.assertEqual(len(nodes), 1)
        node = nodes[0]
        self.assertTrue(isinstance(node, Node))
        self.assertEqual(node.uuid, mock_node.uuid)
        self.assertEqual(node.name, mock_node.name)
        self.assertEqual(node.state, mock_node.state)
        self.assertEqual(node.public_ip, mock_node.public_ip)
        self.assertEqual(node.private_ip, mock_node.private_ip)
        self.assertEqual(node.extra, mock_node.extra)
        self.assertTrue(isinstance(node.driver, IpmiNodeDriver))
        # failed
        self.count['status'] = self.ERROR
        nodes = self.driver.list_nodes()
        self.assertEqual(nodes, [])

    def test_reboot_node(self):
        # on
        self.count = {"status": self.ON, "reset": self.ON}
        self.assertTrue(self.driver.reboot_node(self.mock_nodes[self.ON]))
        # off
        self.count = {"status": self.OFF, "reset": self.OFF}
        self.assertFalse(self.driver.reboot_node(self.mock_nodes[self.OFF]))
        # error
        self.count = {"status": self.ERROR, "reset": self.ERROR}
        self.assertFalse(self.driver.reboot_node(self.mock_nodes[self.ERROR]))

    def test_start_node(self):
        # on
        self.count = {"status": self.ON, "on": self.ON}
        self.assertFalse(self.driver.start_node(self.mock_nodes[self.ON]))
        # off
        self.count = {"status": self.OFF, "on": self.OFF}
        self.assertTrue(self.driver.start_node(self.mock_nodes[self.OFF]))
        # error
        self.count = {"status": self.ERROR, "on": self.ERROR}
        self.assertFalse(self.driver.start_node(self.mock_nodes[self.ERROR]))

    def test_softstop_node(self):
        # on
        self.count = {"status": self.ON, "soft": self.ON}
        self.assertTrue(self.driver.softstop_node(self.mock_nodes[self.ON]))
        # off
        self.count = {"status": self.OFF, "soft": self.OFF}
        self.assertFalse(self.driver.softstop_node(self.mock_nodes[self.OFF]))
        # error
        self.count = {"status": self.ERROR, "soft": self.ERROR}
        self.assertFalse(self.driver.softstop_node(self.mock_nodes[self.ERROR]))

    def test_hardstop_node(self):
        # on
        self.count = {"status": self.ON, "off": self.ON}
        self.assertTrue(self.driver.hardstop_node(self.mock_nodes[self.ON]))
        # off
        self.count = {"status": self.OFF, "off": self.OFF}
        self.assertFalse(self.driver.hardstop_node(self.mock_nodes[self.OFF]))
        # error
        self.count = {"status": self.ERROR, "off": self.ERROR}
        self.assertFalse(self.driver.hardstop_node(self.mock_nodes[self.ERROR]))

if __name__ == '__main__':
    sys.exit(unittest.main())
