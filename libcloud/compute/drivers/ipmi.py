"""
IPMI driver
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

class IpmiNodeDriver(NodeDriver):
    """
    Ipmi node driver
    """

    def __init__(self, key, secret=None, host=None, port=None):
        self.key = key
        self.secret = secret
        self.host = host
        self.port = port
        self.type = Provider.IPMI

    def _get_ipmi_cmd(self,cmd):
        return "ipmitool -H %s -U %s -P %s %s" % (self.host, self.key, self.secret, cmd)

    def _get_state(self):
        state_check_command = self._get_ipmi_cmd("chassis power status")
        (status, output) = commands.getstatusoutput(state_check_command)
        if status == 0:
            state = output.replace("Chassis Power is ", "")
            return state
        else:
            return "unknown"

    def list_nodes(self):
        state = self._get_state()
        if state != "unknown":
            node = Node(1,self.host,self._get_state(),self.host,"",self)                                       
            return [node]
        else:
            return []

    def reboot_node(self,node):
        """
        Reboot the node by passing in the node object
        """
        if self._get_state() == "on":
            reboot_cmd = self._get_ipmi_cmd("chassis power reset")
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
        if self._get_state() == "off":
            start_cmd = self._get_ipmi_cmd("chassis power on")
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
        if self._get_state() == "on":
            softstop_cmd = self._get_ipmi_cmd("chassis power soft")
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
        if self._get_state() == "on":
            hardstop_cmd = self._get_ipmi_cmd("chassis power off")
            (status, output) = commands.getstatusoutput(hardstop_cmd)
            if status == 0:
                return True
            else:
                print output
                return False
        else:
            print "node is not running!"
            return False

