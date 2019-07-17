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
        viewType = [vim.VirtualMachine]  # object types to look for
        recursive = True  # whether we should look into it recursively
        containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)

        children = containerView.view
        mystore = []
        for child in children:
	    print child.runtime.host.name
            mystore.append(child.runtime.host.name)
        return mystore
    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0


