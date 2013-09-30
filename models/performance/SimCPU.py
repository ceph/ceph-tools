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

    def __init__(self, name, cores=1, speed=3 * GIG, ddr=1600):
        """ create an interface simulation
            name -- name of the simulated processor
            cores -- number of cores per chip
            speed -- clock speed in hz
            ddr -- memory transfer rate (in MT/s)
        """

        # wild guess calibration constants
        THREAD = 10             # thread switch time (us)
        PROC = 20               # process switch time (us)
        DMA = 30                # DMA setup and completion time (us)
        HYPER_T = 1.3           # hyper-threading effectivieness
        BUS_WIDTH = 64          # bus width (bits)

        self.desc = "%d core %4.1fGhz %s" % (cores, speed / GIG, name)
        self.cores = cores              # cores per chip
        mhz = speed / MEG               # clock speed (Mhz)
        self.hyperthread = HYPER_T      # hyperthreading multiplier
        width = BUS_WIDTH / 8           # bus width (bytes)

        # estimated time for key operations
        self.bus_bw = speed * width     # max bus transfer rate (B/s)
        self.mem_bw = ddr * MEG * width  # max mem xfr (B/s)
        self.thread_us = THREAD         # thread witch (us)
        self.proc_us = PROC             # process switch (us)
        self.dma_us = DMA               # DMA setup and completion (us)

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
