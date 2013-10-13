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
This is intended to be a simulation of processor speed and throughput
"""

from units import MEG, GIG, SECOND


class CPU:
    """ Performance Modeling NIC or HBA Simulation """

    def __init__(self, name, cores=1, mem=2 * GIG, speed=3 * GIG, ddr=1600):
        """ create an interface simulation
            name -- name of the simulated processor
            cores -- number of cores per processor
            mem -- number of bytes of memory per processor
            speed -- clock speed in hz
            ddr -- memory transfer rate (in MT/s)
        """

        HYPER_T = 1.3           # hyper-threading effectivieness
        BUS_WIDTH = 64          # bus width (bits)

        self.desc = "%d-core %3.1fGhz %s" % (cores, speed / GIG, name)
        self.cores = cores              # cores per processor
        self.mem_size = mem             # memory per processor
        mhz = speed / MEG               # clock speed (Mhz)
        self.hyperthread = HYPER_T      # hyperthreading multiplier
        width = BUS_WIDTH / 8           # bus width (bytes)

        # estimated time for key operations
        self.bus_bw = speed * width     # max bus transfer rate (B/s)
        self.mem_bw = ddr * MEG * width  # max mem xfr (B/s)

        # FIX - wild guess CPU calibration constants
        self.THREAD = 10        # thread switch time (us)
        self.PROC = 20          # process switch time (us)
        self.DMA = 30           # DMA setup and completion time (us)

    def mem_read(self, bytes):
        """ return the elapsed time to read that amount of uncached data """
        bw = min(self.bus_bw, self.mem_bw)
        return bytes * SECOND / bw

    def mem_write(self, bytes):
        """ return the elapsed time to write that amount of data """
        bw = min(self.bus_bw, self.mem_bw)
        return bytes * SECOND / bw

    def process(self, bytes):
        """ return the elapsed time to process that amount of data """
        return bytes * SECOND / self.bus_bw

    def thread_us(self):
        """ return the elapsed time for a thread switch """
        return self.THREAD

    def proc_us(self):
        """ return the elapsed time for a process switch """
        return self.PROC

    def dma_us(self):
        """ return the elapsed time to set-up/complete a DMA operation"""
        return self.DMA

    def queue_length(self, coreload, cores):
        """ return the expected process queue length (per core)
            coreload -- number of cores being used (e.g. 0.75)
            cores -- number of cores available (e.g. 4)
        """
        # FIX ... processor queue length is being modeled as MM1
        rho = coreload / float(cores)
        if (rho < 1):
            avg = rho / (1 - rho)
        else:
            avg = 1000000000   # infinite
        return avg
