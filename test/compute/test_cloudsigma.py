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
import httplib

from libcloud.compute.base import Node
from libcloud.compute.drivers.cloudsigma import CloudSigmaBaseNodeDriver
from libcloud.utils import str2dicts, str2list, dict2str

from test import MockHttp
from test.compute import TestCaseMixin
from test.file_fixtures import ComputeFileFixtures


class CloudSigmaTestCase(unittest.TestCase, TestCaseMixin):
    def setUp(self):
        CloudSigmaBaseNodeDriver.connectionCls.conn_classes = (None,
                                                               CloudSigmaHttp)
        self.driver = CloudSigmaBaseNodeDriver('foo', 'bar')

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertTrue(isinstance(nodes, list))
        self.assertEqual(len(nodes), 1)

        node = nodes[0]
        self.assertEqual(node.public_ip[0], "1.2.3.4")
        self.assertEqual(node.extra['smp'], 1)
        self.assertEqual(node.extra['cpu'], 1100)
        self.assertEqual(node.extra['mem'], 640)

    def test_list_sizes(self):
        images = self.driver.list_sizes()
        self.assertEqual(len(images), 9)

    def test_list_images(self):
        sizes = self.driver.list_images()
        self.assertEqual(len(sizes), 10)

    def test_list_locations_response(self):
        pass

    def test_start_node(self):
        nodes = self.driver.list_nodes()
        node = nodes[0]
        self.assertTrue(self.driver.ex_start_node(node))

    def test_shutdown_node(self):
        nodes = self.driver.list_nodes()
        node = nodes[0]
        self.assertTrue(self.driver.ex_stop_node(node))
        self.assertTrue(self.driver.ex_shutdown_node(node))

    def test_reboot_node(self):
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.reboot_node(node))

    def test_destroy_node(self):
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.destroy_node(node))
        nodes = self.driver.list_nodes()

    def test_create_node(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        node = self.driver.create_node(name = "cloudsigma node", image = image, size = size)
        self.assertTrue(isinstance(node, Node))

    def test_ex_static_ip_list(self):
        ips = self.driver.ex_static_ip_list()
        self.assertEqual(len(ips), 3)

    def test_ex_static_ip_create(self):
        result = self.driver.ex_static_ip_create()
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0].keys()), 6)
        self.assertEqual(len(result[1].keys()), 6)

    def test_ex_static_ip_destroy(self):
        result = self.driver.ex_static_ip_destroy('1.2.3.4')
        self.assertTrue(result)

    def test_ex_drives_list(self):
        result = self.driver.ex_drives_list()
        self.assertEqual(len(result), 2)

    def test_ex_drive_destroy(self):
        result = self.driver.ex_drive_destroy('d18119ce_7afa_474a_9242_e0384b160220')
        self.assertTrue(result)

    def test_ex_set_node_configuration(self):
        node = self.driver.list_nodes()[0]
        result = self.driver.ex_set_node_configuration(node, **{'smp': 2})
        self.assertTrue(result)

    def test_str2dicts(self):
        string = 'mem 1024\ncpu 2200\n\nmem2048\cpu 1100'
        result = str2dicts(string)
        self.assertEqual(len(result), 2)

    def test_str2list(self):
        string = 'ip 1.2.3.4\nip 1.2.3.5\nip 1.2.3.6'
        result = str2list(string)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], '1.2.3.4')
        self.assertEqual(result[1], '1.2.3.5')
        self.assertEqual(result[2], '1.2.3.6')

    def test_dict2str(self):
        d = {'smp': 5, 'cpu': 2200, 'mem': 1024}
        result = dict2str(d)
        self.assertTrue(len(result) > 0)
        self.assertTrue(result.find('smp 5') >= 0)
        self.assertTrue(result.find('cpu 2200') >= 0)
        self.assertTrue(result.find('mem 1024') >= 0)

class CloudSigmaHttp(MockHttp):
    fixtures = ComputeFileFixtures('cloudsigma')

    def _drives_standard_info(self, method, url, body, headers):
        body = self.fixtures.load('drives_standard_info.txt')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _servers_62fe7cde_4fb9_4c63_bd8c_e757930066a0_start(self, method, url, body, headers):
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _servers_62fe7cde_4fb9_4c63_bd8c_e757930066a0_stop(self, method, url, body, headers):
        return (httplib.NO_CONTENT, body, {}, httplib.responses[httplib.OK])

    def _servers_62fe7cde_4fb9_4c63_bd8c_e757930066a0_destroy(self, method, url, body, headers):
         return (httplib.NO_CONTENT, body, {}, httplib.responses[httplib.NO_CONTENT])

    def _drives_d18119ce_7afa_474a_9242_e0384b160220_clone(self, method, url, body, headers):
        body = self.fixtures.load('drives_clone.txt')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _drives_a814def5_1789_49a0_bf88_7abe7bb1682a_info(self, method, url, body, headers):
        body = self.fixtures.load('drives_single_info.txt')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _drives_info(self, method, url, body, headers):
        body = self.fixtures.load('drives_info.txt')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _servers_create(self, method, url, body, headers):
        body = self.fixtures.load('servers_create.txt')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _servers_info(self, method, url, body, headers):
        body = self.fixtures.load('servers_info.txt')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _resources_ip_list(self, method, url, body, headers):
        body = self.fixtures.load('resources_ip_list.txt')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _resources_ip_create(self, method, url, body, headers):
        body = self.fixtures.load('resources_ip_create.txt')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _resources_ip_1_2_3_4_destroy(self, method, url, body, headers):
        return (httplib.NO_CONTENT, body, {}, httplib.responses[httplib.OK])

    def _drives_d18119ce_7afa_474a_9242_e0384b160220_destroy(self, method, url, body, headers):
        return (httplib.NO_CONTENT, body, {}, httplib.responses[httplib.OK])

    def _servers_62fe7cde_4fb9_4c63_bd8c_e757930066a0_set(self, method, url, body, headers):
        body = self.fixtures.load('servers_set.txt')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())