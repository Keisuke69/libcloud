"""
VMware vSphere driver
"""

#from libcloud.common.base import XmlResponse, ConnectionUserAndKey
#from libcloud.common.types import InvalidCredsError, LibcloudError
from libcloud.compute.providers import Provider
from libcloud.compute.types import NodeState
from libcloud.compute.base import Node, NodeDriver, NodeLocation
#from libcloud.compute.base import NodeSize, NodeImage, NodeAuthPassword
from psphere.client import Client
from psphere.managedobjects import HostSystem

class VSphereNodeDriver(NodeDriver):
    """
    VMware vSphere node driver
    """

    NODE_STATE_MAP = {
        'poweredOn': NodeState.RUNNING,
        'poweredOff': NodeState.UNKNOWN,
        'suspended': NodeState.PENDING,
    }
    NODE_STATUS_MAP = {
        'poweredOn': 'running',
        'poweredOff': 'stopped',
        'suspended': 'suspended',
    }

    type = Provider.VSPHERE

    def __init__(self, key, secret=None, secure=True, host=None):
        self.key = key
        self.secret = secret
        self.host = host
        self.connection = Client(server = host, username = key, password = secret)

    def _to_node(self, vm):
        vnc_enabled = False
        for config in vm.config.extraConfig:
            if config.key == "RemoteDisplay.vnc.enabled" and config.value.lower() == "true":
                vnc_enabled = True
        n = Node(
            id = vm.config.uuid,
            name = vm.name,
            state = self.NODE_STATE_MAP[vm.runtime.powerState],
            public_ips = [],
            private_ips = [],
            driver = self,
            extra = {
                'managedObjectReference': vm,
                'status': self.NODE_STATUS_MAP[vm.runtime.powerState],
                'cpu': vm.summary.config.numCpu,
                'memory': vm.summary.config.memorySizeMB * 1024**2,
                'vmPathName': vm.summary.config.vmPathName,
                'vncEnabled': vnc_enabled,
            }
        )
        return n

    def _to_hardware_profile(self, host):
        datastores = []
        for ds in host.datastore:
            datastores.append({
                'name': ds.name,
                'freeSpace': ds.summary.freeSpace,
                'capacity': ds.summary.capacity,
                'type': ds.summary.type,
            })
        hardware_profile = {
            'name': host.name,
            'cpu': host.hardware.cpuInfo.numCpuThreads,
            'memory': host.hardware.memorySize,
            'datastores': datastores,
        }
        return hardware_profile

    def list_nodes(self):
        nodes = []
        hosts = HostSystem.all(self.connection)
        for host in hosts:
            for vm in host.vm:
                nodes.append(self._to_node(vm))
        return nodes

    def reboot_node(self, node):
        vm = node.extra['managedObjectReference']
        task = vm.ResetVM_Task()
        return not task.info.error

    def ex_start_node(self, node):
        vm = node.extra['managedObjectReference']
        task = vm.PowerOnVM_Task()
        return not task.info.error

    def ex_stop_node(self, node):
        vm = node.extra['managedObjectReference']
        task = vm.PowerOffVM_Task()
        return not task.info.error

    def ex_suspend_node(self, node):
        vm = node.extra['managedObjectReference']
        task = vm.SuspendVM_Task()
        return not task.info.error

    def ex_hardware_profiles(self):
        hardware_profiles = []
        hosts = HostSystem.all(self.connection)
        for host in hosts:
            hardware_profiles.append(self._to_hardware_profile(host))
        return hardware_profiles

    #def create_node(self, **kwargs):
    #def destroy_node(self, node):
    #def ex_shutdown_node(self, node):

