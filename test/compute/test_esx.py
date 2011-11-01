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

from libcloud.compute.drivers.esx import ESXNodeDriver
from libcloud.compute.base import Node
from test import LibcloudTestCase
import commands
import re

class ESXTests(LibcloudTestCase):

    POWERON, POWEROFF, SUSPEND, ERROR = range(4)
    SUCCESS, FAILED = range(2)

    def setUp(self):
        self.key = 'key'
        self.secret = 'secret'
        self.host = '127.0.0.1'
        self.driver = ESXNodeDriver(self.key, self.secret, self.host)
        self.count = {"getstate -q":0, "-l":0, "-p":0, "start":0, "stop soft":0, "stop hard":0, "reset soft":0, "suspend soft":0}
        commands.getstatusoutput = Mock(side_effect = self.mock_vmware_cmd)
        self.mock_nodes = [Node(1,"/vmfs/volumes/xxx/vm01/vm01.vmx",'','','',self.driver),
                           Node(2,"/vmfs/volumes/xxx/vm02/vm02.vmx",'','','',self.driver),
                           Node(3,"/vmfs/volumes/xxx/vm03/vm03.vmx",'','','',self.driver),
                           Node(999,"xxx.vmx",'','','',self.driver)]
        self.iter = {}
        self.iter['-l'] = [(0, "\n/vmfs/volumes/xxx/vm01/vm01.vmx\n/vmfs/volumes/xxx/vm02/vm02.vmx\n/vmfs/volumes/xxx/vm03/vm03.vmx"),
                           (1, "Error connecting to server at 'https://127.0.0.1/sdk/webService': Bad hostname")]
        self.iter['-p'] = [(0, "\non 1 1024 /vmfs/volumes/xxx/vm01/vm01.vmx VM01 machine name\noff 2 2048 /vmfs/volumes/xxx/vm02/vm02.vmx VM02\nsuspend 1 512 /vmfs/volumes/xxx/vm03/vm03.vmx VM03"),
                           (1, "Error connecting to server at 'https://127.0.0.1/sdk/webService': Bad hostname")]
        self.iter['getstate -q'] = [(0, "on"), (0, "off"), (0, "suspended"), (1, "No virtual machine found.")]
        self.iter['start'] = [None, (0, "start() = 1"), (0, "start() = 1"), (1, "The attempted operation cannot be performed in the current state.")]
        self.iter['stop soft'] = [(0, "stop() = 1"), None, None, (1, "The attempted operation cannot be performed in the current state.")]
        self.iter['stop hard'] = [(0, "stop() = 1"), None, None, (1, "The attempted operation cannot be performed in the current state.")]
        self.iter['reset soft'] = [(0, "reset() = 1"), None, None, (1, "The attempted operation cannot be performed in the current state.")]
        self.iter['suspend soft'] = [(0, "suspend() = 1"), None, None, (1, "The attempted operation cannot be performed in the current state.")]

    def mock_vmware_cmd(self, str):
        if(str.startswith("vmware-cmd ")):
            command = str.replace("vmware-cmd -H %s -U %s -P %s " % (self.host, self.key, self.secret), "")
            if command.find(".vmx ") != -1:
                command = command.rsplit(".vmx ", 1)[1]
            if(self.iter.has_key(command) and self.count.has_key(command)):
                return self.iter[command][self.count[command]]
            else:
                return (0, "Usage: vmware-cmd <options> <vm-cfg-path> <vm-action> <arguments>\n")
        else:
            return (127, "%s: command not found" % str)

    def test_list_nodes(self):
        # success
        self.count = {"getstate -q": self.POWERON, "-l": self.SUCCESS}
        nodes = self.driver.list_nodes()
        self.assertTrue(isinstance(nodes, list))
        self.assertEqual(len(nodes), 3)
        for node, mock_node in zip(nodes, self.mock_nodes):
            self.assertTrue(isinstance(node, Node))
            self.assertEqual(node.uuid, mock_node.uuid)
            self.assertEqual(node.name, mock_node.name)
            self.assertEqual(node.state, mock_node.state)
            self.assertEqual(node.public_ip, mock_node.public_ip)
            self.assertEqual(node.private_ip, mock_node.private_ip)
            self.assertEqual(node.extra, mock_node.extra)
            self.assertTrue(isinstance(node.driver, ESXNodeDriver))
        # failed
        self.count = {"getstate -q": self.ERROR, "-l": self.FAILED}
        nodes = self.driver.list_nodes()
        self.assertEqual(nodes, [])

    def test_list_nodes_extend(self):
        # success
        self.count = {"getstate -q": self.POWERON, "-p": self.SUCCESS}
        nodes = self.driver.list_nodes_extend()
        self.assertTrue(isinstance(nodes, list))
        self.assertEqual(len(nodes), 3)
        for node, mock_node in zip(nodes, self.mock_nodes):
            self.assertTrue(isinstance(node, Node))
            self.assertEqual(node.uuid, mock_node.uuid)
            self.assertEqual(node.state, mock_node.state)
            self.assertEqual(node.public_ip, mock_node.public_ip)
            self.assertEqual(node.private_ip, mock_node.private_ip)
            self.assertEqual(node.extra, mock_node.extra)
            self.assertTrue(isinstance(node.driver, ESXNodeDriver))
            params = node.name.split(" ", 4)
            self.assertEqual(len(params), 5)
        # failed
        self.count = {"getstate -q": self.ERROR, "-p": self.FAILED}
        nodes = self.driver.list_nodes_extend()
        self.assertEqual(nodes, [])

    def test_reboot_node(self):
        # power on
        self.count = {"getstate -q": self.POWERON, "reset soft": self.POWERON}
        self.assertTrue(self.driver.reboot_node(self.mock_nodes[self.POWERON]))
        # power off
        self.count = {"getstate -q": self.POWEROFF, "reset soft": self.POWEROFF}
        self.assertFalse(self.driver.reboot_node(self.mock_nodes[self.POWEROFF]))
        # suspend
        self.count = {"getstate -q": self.SUSPEND, "reset soft": self.SUSPEND}
        self.assertFalse(self.driver.reboot_node(self.mock_nodes[self.SUSPEND]))
        # not exist
        self.count = {"getstate -q": self.ERROR, "reset soft": self.ERROR}
        self.assertFalse(self.driver.reboot_node(self.mock_nodes[self.ERROR]))

    def test_start_node(self):
        # power on
        self.count = {"getstate -q": self.POWERON, "start": self.POWERON}
        self.assertFalse(self.driver.start_node(self.mock_nodes[self.POWERON]))
        # power off
        self.count = {"getstate -q": self.POWEROFF, "start": self.POWEROFF}
        self.assertTrue(self.driver.start_node(self.mock_nodes[self.POWEROFF]))
        # suspend
        self.count = {"getstate -q": self.SUSPEND, "start": self.SUSPEND}
        self.assertTrue(self.driver.start_node(self.mock_nodes[self.SUSPEND]))
        # not exist
        self.count = {"getstate -q": self.ERROR, "start": self.ERROR}
        self.assertFalse(self.driver.start_node(self.mock_nodes[self.ERROR]))

    def test_softstop_node(self):
        # power on
        self.count = {"getstate -q": self.POWERON, "stop soft": self.POWERON}
        self.assertTrue(self.driver.softstop_node(self.mock_nodes[self.POWERON]))
        # power off
        self.count = {"getstate -q": self.POWEROFF, "stop soft": self.POWEROFF}
        self.assertFalse(self.driver.softstop_node(self.mock_nodes[self.POWEROFF]))
        # suspend
        self.count = {"getstate -q": self.SUSPEND, "stop soft": self.SUSPEND}
        self.assertFalse(self.driver.softstop_node(self.mock_nodes[self.SUSPEND]))
        # not exist
        self.count = {"getstate -q": self.ERROR, "stop soft": self.ERROR}
        self.assertFalse(self.driver.softstop_node(self.mock_nodes[self.ERROR]))

    def test_hardstop_node(self):
        # power on
        self.count = {"getstate -q": self.POWERON, "stop hard": self.POWERON}
        self.assertTrue(self.driver.hardstop_node(self.mock_nodes[self.POWERON]))
        # power off
        self.count = {"getstate -q": self.POWEROFF, "stop hard": self.POWEROFF}
        self.assertFalse(self.driver.hardstop_node(self.mock_nodes[self.POWEROFF]))
        # suspend
        self.count = {"getstate -q": self.SUSPEND, "stop hard": self.SUSPEND}
        self.assertFalse(self.driver.hardstop_node(self.mock_nodes[self.SUSPEND]))
        # not exist
        self.count = {"getstate -q": self.ERROR, "stop hard": self.ERROR}
        self.assertFalse(self.driver.hardstop_node(self.mock_nodes[self.ERROR]))

    def test_softsuspend_node(self):
        # power on
        self.count = {"getstate -q": self.POWERON, "suspend soft": self.POWERON}
        self.assertTrue(self.driver.softsuspend_node(self.mock_nodes[self.POWERON]))
        # power off
        self.count = {"getstate -q": self.POWEROFF, "suspend soft": self.POWEROFF}
        self.assertFalse(self.driver.softsuspend_node(self.mock_nodes[self.POWEROFF]))
        # suspend
        self.count = {"getstate -q": self.SUSPEND, "suspend soft": self.SUSPEND}
        self.assertFalse(self.driver.softsuspend_node(self.mock_nodes[self.SUSPEND]))
        # not exist
        self.count = {"getstate -q": self.ERROR, "suspend soft": self.ERROR}
        self.assertFalse(self.driver.softsuspend_node(self.mock_nodes[self.ERROR]))

if __name__ == '__main__':
    sys.exit(unittest.main())
