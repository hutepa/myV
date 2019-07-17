#!/usr/bin/env python

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
	confy = {}
        for child in children:
		if child.config.template == True:
							
#			print child.config.guestFullName
			if 'windows' in child.config.guestId:
				print child.config.guestId
#			print child.guest.guestFamily
			print "\n"
			
	return mystore
    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0

all()
