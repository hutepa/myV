#!/usr/bin/env python

import atexit

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

#import tools.cli as cli


def all():

    try:
        service_instance = connect.SmartConnectNoSSL(host='xx.xx.xx.xx',
                                                     user='mahmoud@vsphere.local',
                                                     pwd='password',
                                                     port='443')

        atexit.register(connect.Disconnect, service_instance)

        content = service_instance.RetrieveContent()

        container = content.rootFolder
        viewType = [vim.VirtualMachine] 
        recursive = True  
        containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)

        children = containerView.view
        templates = {}
        for child in children:
            if child.config.template == True:
                if 'windows' in child.config.guestId:
                    gid = "Windows"
                else:
                    gid = "Linux"
                cnf = vars(child.summary.config)
                templates[cnf['name']] = [cnf['name'], cnf['numCpu'], cnf['memorySizeMB'],
                                          cnf['numEthernetCards'], cnf['numVirtualDisks'], gid]
        return templates
    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0


