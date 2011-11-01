"""
ESX/ESXi driver
"""

from libcloud.utils import fixxpath, findtext, findattr, findall
from libcloud.common.base import ConnectionUserAndKey
from libcloud.common.aws import AWSBaseResponse
from libcloud.common.types import (InvalidCredsError, MalformedResponseError, LibcloudError)
from libcloud.compute.providers import Provider
from libcloud.compute.types import NodeState
from libcloud.compute.base import Node, NodeDriver, NodeLocation, NodeSize
from libcloud.compute.base import NodeImage
import commands

class ESXNodeDriver(NodeDriver):
    """
    ESX node driver
    """
    
    def __init__(self, key, secret=None, host=None):
        self.key = key
        self.secret = secret
        self.host = host
        self.type = Provider.ESX

    def _get_vmware_cmd(self, cmd, node=None):
        if node is None:
            node_name = ""
        else:
            node_name = node.name + " "
        return "vmware-cmd -H %s -U %s -P %s %s%s" % (self.host, self.key, self.secret, node_name, cmd)

    def _get_state(self,node):
        state_check_command = self._get_vmware_cmd("getstate -q", node)
        (status, output) = commands.getstatusoutput(state_check_command)
        if status == 0:
            node_state = output
        else:
            node_state = "unknown"
        return node_state

    def list_nodes(self):
        get_list_command = self._get_vmware_cmd("-l")
        (status, output) = commands.getstatusoutput(get_list_command)
        if status != 0:
            print output
            return []
        node_names = output.splitlines()
        nodes = []
        id = 0
        for node_name in node_names:
            if node_name == "":
                continue
            id += 1
            #public_ip = self._get_vmware_cmd("%s getguestinfo ip" % (node_name))
            #(status, output) = commands.getstatusoutput(self._get_vmware_cmd("%s getstate" % (node_name)))
            #if status == 0:
            #    node_state = output.replace("getstate() = ", "")
            #else:
            #    node_state = "unknown"
            node = Node(id,node_name,"","","",self)
            nodes.append(node)
        return nodes

    def list_nodes_extend(self):
        get_list_command = self._get_vmware_cmd("-p")
        (status, output) = commands.getstatusoutput(get_list_command)
        if status != 0:
            print output
            return []
        node_names = output.splitlines()
        nodes = []
        id = 0
        for node_name in node_names:
            if node_name == "":
                continue
            id += 1
            #public_ip = self._get_vmware_cmd("%s getguestinfo ip" % (node_name))
            #(status, output) = commands.getstatusoutput(self._get_vmware_cmd("%s getstate" % (node_name)))
            #if status == 0:
            #    node_state = output.replace("getstate() = ", "")
            #else:
            #    node_state = "unknown"
            node = Node(id,node_name,"","","",self)
            nodes.append(node)
        return nodes

    def reboot_node(self,node):
        """
        Reboot the node by passing in the node object
        """
        if self._get_state(node) == "on":
            reboot_cmd = self._get_vmware_cmd("reset soft", node)
            (status, output) = commands.getstatusoutput(reboot_cmd)
            if status == 0:
                return True
            else:
                print output
                return False
        else:
            print "node is not running!"
            return False
        
    def start_node(self,node):
        state = self._get_state(node)
        if state == "off" or state == "suspended":
            start_cmd = self._get_vmware_cmd("start", node)
            (status, output) = commands.getstatusoutput(start_cmd)
            if status == 0:
                return True
            else:
                print output
                return False
        else:
            print "node is running!"
            return False
       
    def softstop_node(self,node):
        if self._get_state(node) == "on":
            softstop_cmd = self._get_vmware_cmd("stop soft", node)
            (status, output) = commands.getstatusoutput(softstop_cmd)
            if status == 0:
                return True
            else:
                print output
                return False
        else:
            print "node is not running!"
            return False

    def hardstop_node(self,node):
        if self._get_state(node) == "on":
            hardstop_cmd = self._get_vmware_cmd("stop hard", node)
            (status, output) = commands.getstatusoutput(hardstop_cmd)
            if status == 0:
                return True
            else:
                print output
                return False
        else:
            print "node is not running!"
            return False

    def softsuspend_node(self,node):
        if self._get_state(node) == "on":
            softsuspend_cmd = self._get_vmware_cmd("suspend soft", node)
            (status, output) = commands.getstatusoutput(softsuspend_cmd)
            if status == 0:
                return True
            else:
                print output
                return False
        else:
            print "node is not running!"
            return False
           
