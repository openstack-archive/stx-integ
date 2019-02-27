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

class numa_cell:
    def __init__(self, id, cpuset, cpu_pinning, shared_vcpu,
        shared_pcpu_for_vcpu):
        self.id = id
        self.cpuset = cpuset
        self.cpu_pinning = cpu_pinning
        self.shared_vcpu = shared_vcpu
        self.shared_pcpu_for_vcpu = shared_pcpu_for_vcpu

class numa_topology:
    def __init__(self, uuid, cells):
        self.instance_uuid = uuid
        self.cells = cells

    def vcpu_to_pcpu(self, vcpu):
        for cell in self.cells:
            if vcpu in cell.cpu_pinning.keys():
                return cell, cell.cpu_pinning[vcpu]
            if vcpu == cell.shared_vcpu:
                return cell, cell.shared_pcpu_for_vcpu
        raise KeyError('Unable to find pCPU for vCPU %d' % vcpu)

class pci_device:
    def __init__(self, numa_node, addr, dev_type,
                 vendor_id, product_id):
        self.numa_node = numa_node
        self.address = addr
        self.dev_id = None
        self.dev_type = dev_type
        self.vendor_id = vendor_id
        self.product_id = product_id

class instance:
    def __init__(self, uuid, name, extra_spec):
        self.uuid = uuid
        self.name = name
        self.extra_spec = extra_spec
        self.pci_devices = set()
        self.numa_topology = None

    def create_pci_devs_info(self, pcidev_str):
        """
        Read pci device info from extra spec string and
        create pci_devices set attribute for instance obj.
        """
        if pcidev_str.startswith('node') is not True:
            LOG.warning("This instance has no pci dev info!")
            return

        try:
            # split to get several devices info.
            DevStrSet = pcidev_str.split('\n')
            LOG.debug(DevStrSet)
            for DevStr in DevStrSet:
                strSet = DevStr.split(',')
                strDict = {}
                for _str in strSet:
                    _strset = _str.strip().split(':',1)
                    strDict[_strset[0]] = _strset[1]

                LOG.debug(strDict)
                pci_dev = pci_device(strDict['node'], strDict['addr'],
                             strDict['type'], strDict['vendor'],
                             strDict['product'])
                self.pci_devices.update([pci_dev])
        except Exception as e:
            LOG.error("Failed to READ pci dev info!! error=%s" % e)
            return

    def range_to_list(self, csv_range=None):
        """
        Convert a string of comma separate ranges into an expanded list of
        integers.  E.g., '1-3,8-9,15' is converted to [1,2,3,8,9,15]
        """
        if not csv_range:
            return []
        xranges = [(lambda L: range(L[0], L[-1] + 1))(map(int, r.split('-')))
                   for r in csv_range.split(',')]
        return [y for x in xranges for y in x]

    def create_numa_topology_info(self, numa_topo):
        """
        str is like below:
        node:1,   512MB, pgsize:2M, 1s,2c,2t, vcpus:0-3, pcpus:59,23,65,29,
              siblings:{0,1},{2,3}, pol:ded, thr:pre
        """
        cells = set()

        if numa_topo.startswith('node') is not True:
            LOG.debug("Could not get numa topology info!")
            return

        # split to get several cells
        strlist = numa_topo.split('\n')
        LOG.debug("numalist:%s" % strlist)
        for _str in strlist:
            strlist1 = _str.split(' ')
            cpusetstr = ''
            pcpusetstr = ''

            for str1 in strlist1:
                str2 = str1.lstrip().rstrip(',').split(':',1)
                if str2[0] == 'node':
                    cell_id = str2[1]
                elif str2[0] == 'vcpus':
                    cpusetstr = str2[1]
                elif str2[0] == 'pcpus':
                    pcpusetstr = str2[1]

            cpuset = []
            cpu_pinning = {}

            if len(cpusetstr):
                cpuset = self.range_to_list(cpusetstr)
                if len(pcpusetstr):
                    pcpulist = pcpusetstr.split(',')
                    for vcpu in cpuset:
                        cpu_pinning[vcpu] = int(pcpulist[vcpu])

            cell = numa_cell(int(cell_id), cpuset, cpu_pinning, None, None)
            LOG.debug("cell_id=%s, vcpuset=%s, cpu_pinning=%s"
                    % (cell_id,cpuset,cpu_pinning))
            cells.update([cell])

        self.numa_topology = numa_topology(self.uuid, cells)

    def create(self, server):
        # get pci device info from attribute string of 'wrs-res:pci_devices'
        # get numa topology info from attribute string of 'wrs-res:topology'
        try:
            _pciDevStr = getattr(server, 'wrs-res:pci_devices')
            _numaStr = getattr(server, 'wrs-res:topology')
        except Exception as e:
            LOG.error('No attribute of wrs-res:pci_devices or wrs-res:topology for instance!!!'
                      'error=%s' % e)
            return

        self.create_pci_devs_info(_pciDevStr)
        self.create_numa_topology_info(_numaStr)

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

