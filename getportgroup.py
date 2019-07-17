#!/usr/bin/env python

import atexit

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

#import tools.cli as cli


def all():

    try:
        si = connect.SmartConnectNoSSL(host='xx.xx.xx.xx',
                                                     user='mahmoud@vsphere.local',
                                                     pwd='password',
                                                     port='443')

        atexit.register(connect.Disconnect, si)
        pgroup = []
        datacenters = si.RetrieveContent().rootFolder.childEntity
        for datacenter in datacenters:
            networks = datacenter.networkFolder.childEntity
            for network in networks:
                pgroup.append(network.name)
                #print network.name
        return pgroup
    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0

#all()
