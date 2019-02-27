#
# Copyright (c) 2019 StarlingX.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

# All Rights Reserved.
#

""" Define instance related class"""

from nova import exception
from novaclient import client
from Log import LOG
import guest

class numa_cell:
    def __init__(self, id, cpuset, cpu_pinning):
        self.id = id
        self.cpuset = cpuset
        self.cpu_pinning = cpu_pinning

class numa_topology:
    def __init__(self, uuid, cells):
        self.instance_uuid = uuid
        self.cells = cells

    def vcpu_to_pcpu(self, vcpu):
        for cell in self.cells:
            if vcpu in cell.cpu_pinning.keys():
                return cell, cell.cpu_pinning[vcpu]
        raise KeyError('Unable to find pCPU for vCPU %d' % vcpu)

class pci_device:
    def __init__(self, addr):
        self.address = addr
        self.dev_id = ""
        self.dev_type = ""
        self.vendor_id = ""
        self.product_id = ""

class instance:
    def __init__(self, uuid, name, extra_spec):
        self.uuid = uuid
        self.name = name
        self.extra_spec = extra_spec
        self.pci_devices = set()
        self.numa_topology = None

    def create(self, server):
        # get numa topology and pci info from libvirt
        cells = set()
        domain = guest.get_libvirt_domain_info(self.uuid)
        for node_id in domain['nodelist']:
            cell = numa_cell(node_id, range(domain['vcpus']), domain['cpu_pinning'])
            LOG.debug("cell_id=%s, vcpuset=%s, cpu_pinning=%s"
                    % (cell_id, cpuset, cpu_pinning))
            cells.update([cell])

        self.numa_topology = numa_topology(self.uuid, cells)

        for pci_addr in domain['pci_set']:
            pci_dev = pci_device(pci_addr)
            self.pci_devices.update([pci_dev])

    def get_cpu_policy(self):
        if 'hw:cpu_policy' in self.extra_spec:
            return self.extra_spec['hw:cpu_policy']
        else:
            return None

    def get_numa_topology(self):
        return self.numa_topology

    def get_extra_spec(self):
        return self.extra_spec

    def get_pci_devices(self):
        return self.pci_devices
