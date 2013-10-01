#
# Ceph - scalable distributed file system
#
# Copyright (C) Inktank
#
# This is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 2.1, as published by the Free Software
# Foundation.  See file COPYING.
#

"""
This is intended to be a simulation of an arbitrary network
interface or HBA, along with the s/w costs of using it (which
could include the costs of the protocol stack).
"""

import SimCPU
from units import MEG, GIG, SECOND


class IFC:
    """ Performance Modeling NIC or HBA Simulation """

    def __init__(self, name, bw=1 * GIG, processor=None):
        """ create an interface simulation
            name -- name of the simulated device
            bw -- max read/write (bytes/sec)
            processor -- processor we're connected to
        """

        self.desc = name
        self.max_read_bw = bw
        self.max_write_bw = bw

        if processor is None:
            self.cpu = SimCPU.CPU("generic")
        else:
            self.cpu = processor

        self.min_read_cpu = self.cpu.dma_us + self.cpu.thread_us
        self.min_write_cpu = self.cpu.dma_us + self.cpu.thread_us

        self.cpu_per_mb_read = 0    # CPU cost to read one MiB (us)
        self.cpu_per_mb_write = 0   # CPU cost to write one MiB (us)
        self.min_read_latency = 5   # minimum latency (us) FIX - madeup
        self.min_write_latency = 5  # minimum latency (us) FIX - madeup

    def read_time(self, bytes):
        """ return the elapsed time for the specified transfer """
        return self.min_read_latency + (SECOND * bytes / self.max_read_bw)

    def read_cpu(self, bytes):
        """ return the CPU cost for the specified transfer """
        return self.min_read_cpu + (bytes * self.cpu_per_mb_read / MEG)

    def write_time(self, bytes):
        """ return the elapsed time for the specified transfer """
        return self.min_write_latency + (SECOND * bytes / self.max_write_bw)

    def write_cpu(self, bytes):
        """ return the CPU cost for the specified transfer """
        return self.min_write_cpu + (bytes * self.cpu_per_mb_write / MEG)


class NIC(IFC):

    def __init__(self, name="NIC", bw=10 * GIG, processor=None):
        """ create an Network Interface Card simulation
            name -- name of the simulated device
            bw -- max read/write (bits/sec)
            processor -- processor we're connected to
        """

        n = "%dGb %s" % (bw / GIG, name)
        IFC.__init__(self, n, bw / 8, processor)

        # TCP is very expensive
        tcpr_mem = 2    # FIX - made up multipler
        tcpw_mem = 2    # FIX - made up multipler
        tcpr_cpu = 5    # FIX - made up multipler
        tcpw_cpu = 5    # FIX - made up multipler
        self.cpu_per_mb_read = tcpr_mem * self.cpu.mem_read(MEG)
        self.cpu_per_mb_read += tcpr_cpu * self.cpu.process(MEG)
        self.cpu_per_mb_write = tcpw_mem * self.cpu.mem_write(MEG)
        self.cpu_per_mb_write += tcpw_cpu * self.cpu.process(MEG)


class HBA(IFC):
    def __init__(self, name="HBA", bw=16 * GIG, processor=None):
        """ create an HBA simulation
            name -- name of the simulated device
            bw -- max read/write (bits/sec)
            processor -- processor we're connected to
        """

        n = "%dGb %s" % (bw / GIG, name)
        IFC.__init__(self, n, bw / 8, processor=processor)
