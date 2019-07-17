from pyVmomi import vim
from pyVmomi import vmodl
#from tools import tasks
from pyVim.connect import SmartConnectNoSSL, Disconnect
import atexit
import argparse
import getpass




def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


def add_nic(si, vm, network):
    """
    :param si: Service Instance
    :param vm: Virtual Machine Object
    :param network: Virtual Network
    """
    spec = vim.vm.ConfigSpec()
    nic_changes = []

    nic_spec = vim.vm.device.VirtualDeviceSpec()
    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

    nic_spec.device = vim.vm.device.VirtualE1000()

    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.deviceInfo.summary = 'vCenter API test'

    nic_spec.device.backing = \
        vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
    nic_spec.device.backing.useAutoDetect = False
    content = si.RetrieveContent()
    nic_spec.device.backing.network = get_obj(content, [vim.Network], network)
    nic_spec.device.backing.deviceName = network

    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nic_spec.device.connectable.startConnected = True
    nic_spec.device.connectable.startConnected = True
    nic_spec.device.connectable.allowGuestControl = True
    nic_spec.device.connectable.connected = False
    nic_spec.device.connectable.status = 'untried'
    nic_spec.device.wakeOnLanEnabled = True
    nic_spec.device.addressType = 'assigned'

    nic_changes.append(nic_spec)
    spec.deviceChange = nic_changes
    e = vm.ReconfigVM_Task(spec=spec)
    print "NIC CARD ADDED"


def main():

    # connect this thing
    serviceInstance = SmartConnectNoSSL(host='xx.xx.xx.xx',
                            user='mahmoud@vsphere.local',
                            pwd='password',
                            port='443')
    # disconnect this thing
    atexit.register(Disconnect, serviceInstance)
    vm_name = "walad"
    port_group = "ent_101_28"
    vm = None
    content = serviceInstance.RetrieveContent()
    vm = get_obj(content, [vim.VirtualMachine], vm_name)

    if vm:
        add_nic(serviceInstance, vm, port_group )
    else:
        print "VM not found"

# start this thing
if __name__ == "__main__":
    main()