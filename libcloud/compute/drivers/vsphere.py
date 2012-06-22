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
import suds

class VSphereNodeDriver(NodeDriver):
    """
    VMware vSphere node driver
    """

    NODE_STATE_MAP = {
        'poweredOn': NodeState.RUNNING,
        'poweredOff': NodeState.TERMINATED,
        'suspended': NodeState.TERMINATED,
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
        public_ips = []
        if vm.guest.toolsRunningStatus == "guestToolsRunning" and hasattr(vm.guest, "net"):
            for network in vm.guest.net:
                if hasattr(network, "ipConfig"):
                    public_ips.extend([ip.ipAddress for ip in network.ipConfig.ipAddress if ip.state == "preferred"])
                elif hasattr(network, "ipAddress"):
                    public_ips.extend([ip for ip in network.ipAddress])
        quickStats = vm.summary.quickStats
        cpu_usage = quickStats.overallCpuUsage if hasattr(quickStats, "overallCpuUsage") else 0
        memory_usage = quickStats.guestMemoryUsage * 1024**2 if hasattr(quickStats, "guestMemoryUsage") else 0
        n = Node(
            id = vm.config.uuid,
            name = vm.name,
            state = self.NODE_STATE_MAP[vm.runtime.powerState],
            public_ips = public_ips,
            private_ips = [],
            driver = self,
            extra = {
                'managedObjectReference': vm,
                'status': self.NODE_STATUS_MAP[vm.runtime.powerState],
                'cpu': vm.summary.config.numCpu,
                'memory': vm.summary.config.memorySizeMB * 1024**2,
                'vmPathName': vm.summary.config.vmPathName,
                'vncEnabled': vnc_enabled,
                'toolsRunningStatus': str(vm.guest.toolsRunningStatus),
                'toolsVersionStatus': str(vm.guest.toolsVersionStatus),
                'max_cpu_usage': vm.summary.runtime.maxCpuUsage,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
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
            'max_cpu_usage': host.summary.hardware.cpuMhz * host.summary.hardware.numCpuCores,
            'cpu_usage': host.summary.quickStats.overallCpuUsage,
            'memory_usage': host.summary.quickStats.overallMemoryUsage * 1024**2,
        }
        return hardware_profile

    def list_nodes(self, ex_node_ids = None):
        nodes = []
        hosts = HostSystem.all(self.connection)
        for host in hosts:
            for vm in host.vm:
                node = self._to_node(vm)
                if not ex_node_ids or node.id in ex_node_ids:
                    nodes.append(node)
        return nodes

    def reboot_node(self, node):
        vm = node.extra['managedObjectReference']
        try:
            vm.RebootGuest()
            return True
        except suds.WebFault:
            return False

    def destroy_node(self, node):
        vm = node.extra['managedObjectReference']
        try:
            vm.UnregisterVM()
            return True
        except suds.WebFault:
            return False

    def ex_start_node(self, node):
        vm = node.extra['managedObjectReference']
        try:
            task = vm.PowerOnVM_Task()
            return task.info.state != "error"
        except suds.WebFault:
            return False

    def ex_stop_node(self, node):
        vm = node.extra['managedObjectReference']
        try:
            task = vm.PowerOffVM_Task()
            return task.info.state != "error"
        except suds.WebFault:
            return False

    def ex_shutdown_node(self, node):
        vm = node.extra['managedObjectReference']
        try:
            vm.ShutdownGuest()
            return True
        except suds.WebFault:
            return False

    def ex_suspend_node(self, node):
        vm = node.extra['managedObjectReference']
        try:
            task = vm.SuspendVM_Task()
            return task.info.state != "error"
        except suds.WebFault:
            return False

    def ex_hardware_profiles(self):
        hardware_profiles = []
        hosts = HostSystem.all(self.connection)
        for host in hosts:
            hardware_profiles.append(self._to_hardware_profile(host))
        return hardware_profiles

    #def create_node(self, **kwargs):
    #def destroy_node(self, node):
    #def ex_shutdown_node(self, node):

