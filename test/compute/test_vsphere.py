import sys
import unittest
from mock import patch, Mock, MagicMock

from libcloud.compute.base import Node
from libcloud.compute.drivers.vsphere import VSphereNodeDriver

from test import LibcloudTestCase
from test.compute import TestCaseMixin

class VSphereTests(LibcloudTestCase):

    def setUp(self):
        self.should_list_locations = False
        self.should_have_pricing = False
        self.patchers = []
        self.patchers.append(patch('libcloud.compute.drivers.vsphere.Client'))
        self.patchers.append(patch('libcloud.compute.drivers.vsphere.HostSystem', new=MockHostSystem))
        for patcher in self.patchers:
            patcher.start()
        self.driver = VSphereNodeDriver(key="key", secret="secret", host="127.0.0.1")
        self.vm = MockVirtualMachine()
        self.node = Node(
            id = "vsphere_uuid",
            name = "vm name",
            state = 0,
            public_ips = [],
            private_ips = [],
            driver = self.driver,
            extra = {
                'managedObjectReference': self.vm,
                'status': 'running',
                'cpu': 1,
                'memory': 2048 * 1024**2,
                'vncEnabled': False,
                'toolsRunningStatus': 'guestToolsRunning',
                'toolsVersionStatus': 'toolsVersionCurrent',
                'max_cpu_usage': 2000,
                'cpu_usage': 100,
                'memory_usage': 300 * 1024**2,
                'vmpath': '[datastore1] /foo/bar.vmx',
                'stucked': 1,
                'question_id': 1,
                'question': "question message",
                'choices': [{'label': 'choice1', 'key': 1, 'summary': 'choice1'}],
            })
        self.maxDiff = None

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def test_to_node(self):
        vm = self.vm
        expect = self.node
        node = self.driver._to_node(vm)
        self.assertEqual(expect.id, node.id)
        self.assertEqual(expect.name, node.name)
        self.assertEqual(expect.state, node.state)
        self.assertEqual(expect.public_ips, node.public_ips)
        self.assertEqual(expect.private_ips, node.private_ips)
        self.assertEqual(expect.driver, node.driver)
        self.assertDictEqual(expect.extra, node.extra)

    def test_to_hardware_profile(self):
        expect = {
            'id': 'hardware_uuid',
            'name': 'host name',
            'cpu': 16,
            'memory': 16 * 1024**3,
            'max_cpu_usage': 16000,
            'cpu_usage': 300,
            'memory_usage': 1000 * 1024**2,
            'datastores': [{'name': 'datastore name', 'freeSpace': 400 * 1024**3, 'capacity': 800 * 1024**3, 'type': 'nfs'}]
        }
        host = MockHostSystem()
        hardware_profile = self.driver._to_hardware_profile(host)
        self.assertDictEqual(expect, hardware_profile)

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertIsInstance(nodes, list)
        self.assertEqual(len(nodes), 1)
        self.assertIsInstance(nodes[0], Node)
        self.assertEqual(nodes[0].driver, self.driver)

    def test_reboot_node(self):
        result = self.driver.reboot_node(self.node)
        self.assertTrue(result)

    def test_destroy_node(self):
        result = self.driver.destroy_node(self.node)
        self.assertTrue(result)

    def test_ex_start_node(self):
        result = self.driver.ex_start_node(self.node)
        self.assertTrue(result)

    def test_ex_stop_node(self):
        result = self.driver.ex_stop_node(self.node)
        self.assertTrue(result)

    def test_ex_shutdown_node(self):
        result = self.driver.ex_shutdown_node(self.node)
        self.assertTrue(result)

    def test_ex_suspend_node(self):
        result = self.driver.ex_suspend_node(self.node)
        self.assertTrue(result)

    def test_ex_answer_node(self):
        result = self.driver.ex_answer_node(self.node, 1)
        self.assertTrue(result)

    def test_ex_hardware_profiles(self):
        hardware_profiles = self.driver.ex_hardware_profiles()
        self.assertIsInstance(hardware_profiles, list)
        self.assertEqual(len(hardware_profiles), 1)
        self.assertIsInstance(hardware_profiles[0], dict)
        self.assertEqual(hardware_profiles[0]["id"], "hardware_uuid")

class MockHostSystem(object):

    def __init__(self):
        self.name = "host name"
        self.datastore = [MockDatastore()]
        self.summary = Mock(**{'hardware.uuid': "hardware_uuid",
                               'hardware.cpuMhz': 2000,
                               'hardware.numCpuCores': 8,
                               'quickStats.overallCpuUsage': 300,
                               'quickStats.overallMemoryUsage': 1000})
        self.hardware = Mock(**{'cpuInfo.numCpuThreads': 16,
                                'memorySize': 16 * 1024**3})
        self.vm = [MockVirtualMachine()]

    @classmethod
    def all(self, client):
        return [MockHostSystem()]

class MockDatastore(object):

    def __init__(self):
        self.name = 'datastore name'
        self.summary = Mock(**{'freeSpace': 400 * 1024**3,
                               'capacity': 800 * 1024**3,
                               'type': 'nfs'})

class MockVirtualMachine(object):

    def __init__(self):
        self.name = "vm name"
        self.summary = Mock(**{'quickStats.overallCpuUsage': 100,
                               'quickStats.guestMemoryUsage': 300,
                               'config.numCpu': 1,
                               'config.memorySizeMB': 2048,
                               'config.vmPathName': '[datastore1] /foo/bar.vmx',
                               'runtime.maxCpuUsage': 2000})
        self.runtime = Mock(**{'powerState': 'poweredOn',
                               'question': Mock(spec=['id', 'choice', 'text'],
                                                **{'id': 1,
                                                   'choice.choiceInfo': [Mock(**{'key': 1, 'label': 'choice1', 'summary': 'choice1'})],
                                                   'text': 'question message'})})
        self.config = Mock(**{'uuid': "vsphere_uuid",
                              'extraConfig': [MagicMock()]})
        self.guest = Mock(**{'toolsRunningStatus': "guestToolsRunning",
                             'toolsVersionStatus': "toolsVersionCurrent",
                             'net': [MagicMock()]})

    def RebootGuest(self):
        pass

    def ShutdownGuest(self):
        pass

    def UnregisterVM(self):
        pass

    def AnswerVM(self, questionId, answerChoice):
        pass

    def PowerOnVM_Task(self):
        return MagicMock()

    def PowerOffVM_Task(self):
        return MagicMock()

    def SuspendVM_Task(self):
        return MagicMock()

if __name__ == '__main__':
    sys.exit(unittest.main())
