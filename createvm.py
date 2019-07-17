#!/usr/bin/env python

from pyVmomi import vim
from pyVim.connect import SmartConnect,SmartConnectNoSSL, Disconnect
import atexit
import argparse
import getpass
import string
import random


def get_args():
    """ Get arguments from CLI """
    parser = argparse.ArgumentParser(
        description='Arguments for talking to vCenter')

    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='vSpehre service to connect to')

    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='Username to use')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='Password to use')

    parser.add_argument('-v', '--vm-name',
                        required=True,
                        action='store',
                        help='Name of the VM you wish to make')

    parser.add_argument('--template',
                        required=True,
                        action='store',
                        help='Name of the template/VM \
                            you are cloning from')

    parser.add_argument('--datacenter-name',
                        required=False,
                        action='store',
                        default=None,
                        help='Name of the Datacenter you\
                            wish to use. If omitted, the first\
                            datacenter will be used.')

    parser.add_argument('--vm-folder',
                        required=False,
                        action='store',
                        default=None,
                        help='Name of the VMFolder you wish\
                            the VM to be dumped in. If left blank\
                            The datacenter VM folder will be used')

    parser.add_argument('--datastore-name',
                        required=False,
                        action='store',
                        default=None,
                        help='Datastore you wish the VM to end up on\
                            If left blank, VM will be put on the same \
                            datastore as the template')

    parser.add_argument('--datastorecluster-name',
                        required=False,
                        action='store',
                        default=None,
                        help='Datastorecluster (DRS Storagepod) you wish the VM to end up on \
                            Will override the datastore-name parameter.')

    parser.add_argument('--cluster-name',
                        required=False,
                        action='store',
                        default=None,
                        help='Name of the cluster you wish the VM to\
                            end up on. If left blank the first cluster found\
                            will be used')

    parser.add_argument('--resource-pool',
                        required=False,
                        action='store',
                        default=None,
                        help='Resource Pool to use. If left blank the first\
                            resource pool found will be used')

    parser.add_argument('--power-on',
                        dest='power_on',
                        required=False,
                        action='store_true',
                        help='power on the VM after creation')

    parser.add_argument('--no-power-on',
                        dest='power_on',
                        required=False,
                        action='store_false',
                        help='do not power on the VM after creation')

    parser.set_defaults(power_on=True)

    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass(
            prompt='Enter password')

    return args


def wait_for_task(task):
    """ wait for a vCenter task to finish """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result

        if task.info.state == 'error':
            print "there was an error"
            task_done = True


def get_obj(content, vimtype, name):
    """
    Return an object by name, if name is None the
    first found object is returned
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break

    return obj


def clone_vm(
        content, template, vm_name,
        datacenter_name, vm_folder, datastore_name,
        cluster_name, power_on, datastorecluster_name,cpus,mem,guestid,nicnum,nics):
    """
    Clone a VM from a template/VM, datacenter_name, vm_folder, datastore_name
    cluster_name, resource_pool, and power_on are all optional.
    """

    # if none git the first one
    datacenter = get_obj(content, [vim.Datacenter], datacenter_name)
    #fprint vm_folder
    destfolder = get_obj(content, [vim.Folder], vm_folder)

    if datastore_name:
        datastore = get_obj(content, [vim.Datastore], datastore_name)
    else:
        datastore = get_obj(
            content, [vim.Datastore], template.datastore[0].info.name)

    # if None, get the first one
    cluster = get_obj(content, [vim.ClusterComputeResource], cluster_name)
    #print guestid
    resource_pool = cluster.resourcePool
    adaptermaps = []
    devices = []

    for i in range(nicnum):
        nicspec = vim.vm.device.VirtualDeviceSpec()
        nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        nicspec.device = vim.vm.device.VirtualVmxnet3()
        nicspec.device.wakeOnLanEnabled = True
        nicspec.device.deviceInfo = vim.Description()
        nicspec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        #print type(nics[i])
        nicspec.device.backing.network = get_obj(content, [vim.Network], str(nics[i]))
        nicspec.device.backing.deviceName = str(nics[i])
        nicspec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nicspec.device.connectable.startConnected = True
        nicspec.device.connectable.allowGuestControl = True
        devices.append(nicspec)
        ##adaptermap = vim.vm.customization.AdapterMapping()
        #adaptermap.adapter = vim.vm.customization.IPSettings(ip=vim.vm.customization.FixedIp(ipAddress='10.220.28.80'),subnetMask='255.255.255.0', gateway='10.220.28.1')
        ##adaptermap.adapter = vim.vm.customization.IPSettings(ip=vim.vm.customization.DhcpIpGenerator())
        ##adaptermaps.append(adaptermap)
    try:
        vmconf = vim.vm.ConfigSpec(numCPUs=cpus, memoryMB=mem)
        print "hay hay"
    except:
        print "couldn't set cpu and mem"
    try:
        vmconf.deviceChange = devices
    except:
        print "couldn't set devices"
    ##globalip = vim.vm.customization.GlobalIPSettings(dnsServerList=['xx.xx.xx.xx', 'xx.xx.xx.xx'])

    ##if 'windows' not in guestid:
        ##ident = vim.vm.customization.LinuxPrep(domain='vsphere.local', hostName=vim.vm.customization.FixedName(name=vm_name))
    ##else:
        ##ident = vim.vm.customization.Sysprep()
        ##ident.guiUnattended = vim.vm.customization.GuiUnattended()
        ##ident.guiUnattended.autoLogon = False  # the machine does not auto-logon
        #ident.guiUnattended.password = vim.vm.customization.Password()
        #ident.guiUnattended.password.value = vm_password
        #ident.guiUnattended.password.plainText = True  # the password is not encrypted
        ##ident.userData = vim.vm.customization.UserData()
        ##ident.userData.fullName = "My Name"
        ##ident.userData.orgName = "Company"
        ##ident.userData.computerName = vim.vm.customization.FixedName()
        ##ident.userData.computerName.name = vm_name
        ##ident.identification = vim.vm.customization.Identification()

    ##customspec = vim.vm.customization.Specification(nicSettingMap=adaptermaps, globalIPSettings=globalip,identity=ident)

    if datastorecluster_name:
        podsel = vim.storageDrs.PodSelectionSpec()
        pod = get_obj(content, [vim.StoragePod], datastorecluster_name)
        podsel.storagePod = pod

        storagespec = vim.storageDrs.StoragePlacementSpec()
        storagespec.podSelectionSpec = podsel
        storagespec.type = 'create'
        storagespec.folder = destfolder
        storagespec.resourcePool = resource_pool
        storagespec.configSpec = vmconf

        try:
            rec = content.storageResourceManager.RecommendDatastores(
                storageSpec=storagespec)
            rec_action = rec.recommendations[0].action[0]
            real_datastore_name = rec_action.destination.name
        except:
            real_datastore_name = template.datastore[0].info.name

        datastore = get_obj(content, [vim.Datastore], real_datastore_name)

    # set relospec
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = datastore
    relospec.pool = resource_pool

    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.powerOn = power_on
    ##clonespec.customization = customspec

    print "cloning VM..."
    task = template.Clone(folder=destfolder, name=vm_name, spec=clonespec)
    #wait_for_task(task)


def start(vmname, template_str, cpus, mem, vm_folder, nicnum,nics):
    """
    Let this thing fly

    args = get_args()
    """
    # connect this thing
    si =  SmartConnectNoSSL(host='xx.xx.xx.xx',
                            user='mahmoud@vsphere.local',
                            pwd='password',
                            port='443')
    # disconnect this thing
    atexit.register(Disconnect, si)

    content = si.RetrieveContent()
    template = None

    template = get_obj(content, [vim.VirtualMachine], template_str)

    guestid = template.config.guestId

    dc_name, ds_name, cluster_name, ds_cluster_name = (None for i in range(4))
    power_on = True

    if template:
        clone_vm(
            content, template, vmname,
            dc_name, vm_folder,
            ds_name, cluster_name,
             power_on, ds_cluster_name,cpus, mem, guestid,nicnum,nics)
    else:
        print "template not found"
