#!/usr/bin/env python
# VMware vSphere Python SDK
# Copyright (c) 2008-2013 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Python program for listing the vms on an ESX / vCenter host
"""

import atexit

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

#import tools.cli as cli


def sizeof_fmt(num):
    """
    Returns the human readable version of a file size
    :param num:
    :return:
    """
    for item in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, item)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')

def print_fs(host_fs):
    """
    Prints the host file system volume info
    :param host_fs:
    :return:
    """
    print("{}\t{}\t".format("Datastore:     ", host_fs.volume.name))
    print("{}\t{}\t".format("UUID:          ", host_fs.volume.uuid))
    print("{}\t{}\t".format("Capacity:      ", sizeof_fmt(host_fs.volume.capacity)))
    print("{}\t{}\t".format("VMFS Version:  ", host_fs.volume.version))
    print("{}\t{}\t".format("Is Local VMFS: ", host_fs.volume.local))
    print("{}\t{}\t".format("SSD:           ", host_fs.volume.ssd))

def all():
    """
    Simple command-line program for listing the virtual machines on a system.
    """

    #args = cli.get_args()

    try:
        #if args.disable_ssl_verification:
        service_instance = connect.SmartConnectNoSSL(host='xx.xx.xx.xx',
                                                     user='mahmoud@vsphere.local',
                                                     pwd='password',
                                                     port='443')
        #else:
        #    service_instance = connect.SmartConnectNoSSL(host=args.host,
        #                                            user=args.user,
        #                                            pwd=args.password,
        #                                           port=int(args.port))

        atexit.register(connect.Disconnect, service_instance)

        content = service_instance.RetrieveContent()

        container = content.rootFolder  # starting point to look into
        viewType = [vim.HostSystem]  # object types to look for
        recursive = True  # whether we should look into it recursively
        containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)
        datastores = {}
        children = containerView.view
        mystore = []
        for child in children:
#	    print child.name
            #mystore.append(child.name)
	    storage_system = child.configManager.storageSystem
            host_file_sys_vol_mount_info = \
                storage_system.fileSystemVolumeInfo.mountInfo

            datastore_dict = {}

            # Map all filesystems
            for host_mount_info in host_file_sys_vol_mount_info:
                # Extract only VMFS volumes
                if host_mount_info.volume.type == "VMFS":
			mystore.append(host_mount_info.volume.name)
#                    extents = host_mount_info.volume.extent
#                    print_fs(host_mount_info)

#                    extent_arr = []
#                    extent_count = 0
#                    for extent in extents:
#                           print("{}\t{}\t".format("Extent[" + str(extent_count) + "]:", extent.diskName))
#                           extent_count += 1
#
#                    print
#            # associate ESXi host with the datastore it sees
#            datastores[child.name] = datastore_dict
  
        print mystore   

        return mystore
    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0

