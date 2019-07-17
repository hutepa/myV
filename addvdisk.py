#!/usr/bin/env python

from pyVmomi import vim
from pyVim.connect import SmartConnect,SmartConnectNoSSL, Disconnect
import atexit
import argparse
import getpass
import string
import random
import logging



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
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ips = ['10.220.28.155','10.220.29.154']
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


    # Relocation spec
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = datastore
    relospec.pool = resource_pool

    adaptermaps = []
    devices = []
    devs = []

    for dev in template.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualEthernetCard):
            devs.append(dev)
    #print devices[0]
    for i in range(nicnum):
        # VM device
        nic = vim.vm.device.VirtualDeviceSpec()
        nic.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit  # or edit if a device exists
        nic.device = devs[i] #vim.vm.device.VirtualVmxnet3()
        nic.device.wakeOnLanEnabled = True
        nic.device.addressType = 'assigned'
        #nic.device.key = 4000  # 4000 seems to be the value to use for a vmxnet3 device
        nic.device.deviceInfo = vim.Description()
        #nic.device.deviceInfo.label = "Network Adapter %s" % str(int(i) + 1)
        nic.device.deviceInfo.summary = str(nics[i])
        nic.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        nic.device.backing.network = get_obj(content, [vim.Network], str(nics[i]))
        nic.device.backing.deviceName = str(nics[i])
        nic.device.backing.useAutoDetect = True
        nic.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic.device.connectable.startConnected = True
        nic.device.connectable.allowGuestControl = True
        nic.device.connectable.connected = True
        devices.append(nic)
        #devices[i] = nic
        #if i == 0:
            #print devices[i]

        # guest NIC settings, i.e. "adapter map"
        guest_map = vim.vm.customization.AdapterMapping()
        guest_map.adapter = vim.vm.customization.IPSettings()
        guest_map.adapter.ip = vim.vm.customization.FixedIp()
        guest_map.adapter.ip.ipAddress = ips[i]
        guest_map.adapter.subnetMask = "255.255.255.0"
        #print nic.device.backing.deviceName
        # these may not be set for certain IPs, e.g. storage IPs
        try:
            guest_map.adapter.gateway = '10.220.28.1'
        except:
            pass

        try:
            guest_map.adapter.dnsDomain = 'logistics.intra'
        except:
            pass

        adaptermaps.append(guest_map)

    newvdisks = 2
    scsicount = 0
    vdiskcount = 0

    for dev in template.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualLsiLogicController):
            scsicount += 1
            #print scsicount
            contKey = dev.key
            #print dev
        if isinstance(dev, vim.vm.device.VirtualDisk):
            vdiskcount += 1
            dskKey = dev.key
            #print dev
    if newvdisks > 0:
        for j in range(newvdisks):

            dskKey += 1


            disk = vim.vm.device.VirtualDeviceSpec(
                    fileOperation="create",
                    operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
                    device=vim.vm.device.VirtualDisk(
                        key=dskKey,
                        backing=vim.vm.device.VirtualDisk.FlatVer2BackingInfo(
                            diskMode="persistent",
                            thinProvisioned=True
                            #datastore=vim.Datastore("datastore2")
                        ),
                        capacityInKB=(1024 * 1024),
                        controllerKey=contKey,
                        unitNumber=1,
                        connectable=vim.vm.device.VirtualDevice.ConnectInfo(
                            startConnected=True,
                            allowGuestControl=True,
                            connected=True
                        )
                    )
            )

            #disk = vim.vm.device.VirtualDisk()
            #disk.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            #disk.backing.diskMode = "persistent"
            #disk.capacityInKB = 1024 * 1024
            #print disk
            # This needs to be the current controller on the VM.
            #disk.controllerKey = scsictrlr.device.key
            #print scsictrlr.device.key
            # This must be a VMware datastore object
            #disk.backing.datastore = vim.Datastore("datastore2")

            # This number is a unique number for the disk on the current controller
            #disk.unitNumber = vdiskcount + 1
            vdiskcount += 1
            scsicount += 1
            devices.append(disk)
            #print disk

    #print len(devices)
    #print len(adaptermaps)
    # VM config spec
    vmconf = vim.vm.ConfigSpec()
    vmconf.numCPUs = cpus
    vmconf.memoryMB = mem
    vmconf.cpuHotAddEnabled = True
    vmconf.memoryHotAddEnabled = True
    vmconf.deviceChange = devices
    #print vmconf.deviceChange[1].device.backing.network.name
    #print vmconf.deviceChange[1].device.backing.deviceName
    #print len(vmconf.deviceChange)
    #print vmconf
    # DNS settings
    globalip = vim.vm.customization.GlobalIPSettings()
    globalip.dnsServerList = ['xx.xx.xx.xx','xx.xx.xx.xx']
    globalip.dnsSuffixList = 'logistics.intra'

    # Hostname settings
    ident = vim.vm.customization.LinuxPrep()
    ident.domain = 'logistics.intra'
    ident.hostName = vim.vm.customization.FixedName()
    ident.hostName.name = "kw0tevmwos"

    customspec = vim.vm.customization.Specification()
    customspec.nicSettingMap = adaptermaps
    customspec.globalIPSettings = globalip
    customspec.identity = ident

    # Clone spec
    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.config = vmconf
    clonespec.customization = customspec
    clonespec.powerOn = True
    clonespec.template = False
    #print clonespec

    # fire the clone task
    task = template.Clone(folder=destfolder, name=vm_name, spec=clonespec)
    #result = WaitTask(task, 'VM clone task')
    #result = wait_for_task(task)
    #print result
    # send notification
    # send_email(deploy_settings, ip_settings, output)


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

nics = ['ent_101_28','app_102_29']
start('waskzzxz', "centos7.4docker", 8, 32768, "Cloned", 2, nics)
