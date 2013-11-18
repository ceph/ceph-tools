#!/usr/bin/python
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
        self.clock = speed              # processor clock speed
        self.mem_speed = ddr            # memory speed
        self.hyperthread = HYPER_T      # hyperthreading multiplier
        width = BUS_WIDTH / 8           # bus width (bytes)

        # estimated time for key operations
        self.bus_bw = speed * width     # max bus transfer rate (B/s)
        self.mem_bw = ddr * MEG * width  # max mem xfr (B/s)

        # CPU calibration constants ... expect these to be over-ridden
        self.I_PER_HZ = 6.0             # scaling instruction speed to hz
        self.THREAD = 10                # FIX - thread switch time (us)
        self.PROC = 20                  # FIX - process switch time (us)
        self.DMA = 30                   # FIX - DMA setup/completion time (us)

    def mem_read(self, bytes):
        """ return the elapsed time to read that amount of uncached data """
        bw = min(self.bus_bw, self.mem_bw)
        return float(bytes) * SECOND / bw

    def mem_write(self, bytes):
        """ return the elapsed time to write that amount of data """
        bw = min(self.bus_bw, self.mem_bw)
        return float(bytes) * SECOND / bw

    def process(self, bytes):
        """ return the elapsed time to process that amount of data """
        return float(bytes) * SECOND / self.bus_bw

    def execute(self, instrs):
        """ return the elapsed time to execute # random instructions """
        return float(instrs) * SECOND / (self.clock * self.I_PER_HZ)

    def thread_us(self):
        """ return the elapsed time for a thread switch """
        return self.THREAD

    def proc_us(self):
        """ return the elapsed time for a process switch """
        return self.PROC

    def dma_us(self):
        """ return the elapsed time to set-up/complete a DMA operation"""
        return self.DMA

    def queue_length(self, rho, max_depth=1000):
        """ expected average queue depth as a function of load
            rho -- average fraction of time CPU is busy
            max_depth -- the longest the queue can possibly be
        """
        if (rho >= 1):
            return max_depth
        else:
            avg = rho / (1 - rho)
            return avg if avg < max_depth else max_depth

    #
    # these operations would normally be a function of CPU speed, but
    # may also be off-loaded, improving speed and reducing CPU loading
    #
    def sha_time(self, bytes, width=40):
        """ return the elapsed time for a SHA computation
            bytes -- bytes to be hashed
            width -- desired output hash width
        """
        x = 43           # FIX - recalibrate SHA
        t_cpu = self.execute(x * bytes)
        t_read = self.mem_read(bytes)
        t_write = self.mem_write(width)

        return t_cpu + t_read + t_write

    def sha_cpu(self, bytes, width=40):
        """ return the CPU time for a SHA computation
            bytes -- bytes to be hashed
            width -- desired output hash width
        """
        # w/o acceleration CPU time = clock time
        return self.sha_time(bytes, width)

    def compress_time(self, bytes, comp=2):
        """ return the elapsed time for an LZW-like compression
            bytes -- input block size
            comp -- expected compression factor
        """
        x = 68          # FIX - recalibrate compression
        t_cpu = self.execute(x * bytes)
        t_read = self.mem_read(bytes)
        t_write = self.mem_write(bytes / comp)
        return t_cpu + t_read + t_write

    def compress_cpu(self, bytes, comp=2):
        """ return the cpu time for an LZW-like compression """
        # w/o acceleration CPU time = clock time
        return self.compress_time(bytes, comp)

    def decompress_time(self, bytes, comp=2):
        """ return the elapsed time for an LZW-like decompression
            bytes -- expected output block size
            comp -- expected compression factor
        """
        x = 33          # FIX - recalibrate decompression
        t_cpu = self.execute(x * bytes)
        t_read = self.mem_read(bytes / comp)
        t_write = self.mem_write(bytes)
        return t_cpu + t_read + t_write

    def decompress_cpu(self, bytes, comp=2):
        """ return the cpu time for an LZW-like decompression """
        # w/o acceleration CPU time = clock time
        return self.decompress_time(bytes)

    def raid6_time(self, bytes, n=6, m=2):
        """ return the elapsed time for a RAID-6 write computation """
        x = 10          # FIX - recalibrate RAID-6 computation
        t_cpu = self.execute(x * n * bytes)
        t_read = self.mem_read(n * bytes)
        t_write = self.mem_write(m * bytes)
        return t_cpu + t_read + t_write

    def raid6_cpu(self, bytes, n=6, m=2):
        """ return the cpu time for a RAID-6 write computation """
        # w/o acceleration CPU time = clock time
        return self.raid6_time(bytes, n, m)


def makeCPU(dict):
    """ handy function to instantiate a CPU from parameters in a dict """

    defaults = {
        'cpu': 'Essex',
        'speed': 3 * GIG,
        'cores': 1,
        'mem': 2 * GIG,
        'ddr': 1600,
    }

    # pull the parameters out of the supplied dict
    cpu_type = dict['cpu'] if 'cpu' in dict else defaults['cpu']
    speed = dict['speed'] if 'speed' in dict else defaults['speed']
    cores = dict['cores'] if 'cores' in dict else defaults['cores']
    mem = dict['mem'] if 'mem' in dict else defaults['mem']
    ddr = dict['ddr'] if 'ddr' in dict else defaults['ddr']

    cpu = CPU(cpu_type, speed=speed, cores=cores, mem=mem, ddr=ddr)
    return cpu


#
# basic unit test exerciser
#
if __name__ == '__main__':

    cpu = makeCPU([])
    print("%s w/%dGB of DDR3-%d RAM" %
          (cpu.desc, cpu.mem_size / GIG, cpu.mem_speed))
    print
    print("    thread switch   %dus" % (cpu.thread_us()))
    print("    process switch  %dus" % (cpu.proc_us()))
    print("    DMA start/intr  %dus" % (cpu.dma_us()))

    from Report import Report

    r = Report(("mem-rd", "mem-wrt", "process", "instrs"))
    print
    r.printHeading()
    sizes = [1024, 4096, 128*1024, 1024*1024]
    for bs in sizes:
        mem_r = cpu.mem_read(bs)
        mem_w = cpu.mem_write(bs)
        mem_p = cpu.process(bs)
        mem_x = cpu.execute(bs)
        r.printLatency(bs, (mem_r, mem_w, mem_p, mem_x))

    r = Report(("sha-1", "comp", "decomp", "RAID-6"))
    print
    r.printHeading()
    sizes = [1024, 4096, 128*1024, 1024*1024]
    for bs in sizes:
        sha_t = cpu.sha_time(bs)
        sha_c = cpu.sha_cpu(bs)
        lzwc_t = cpu.compress_time(bs)
        lzwc_c = cpu.compress_cpu(bs)
        lzwd_t = cpu.decompress_time(bs)
        lzwd_c = cpu.decompress_cpu(bs)
        raid_t = cpu.raid6_time(bs)
        raid_c = cpu.raid6_cpu(bs)
        r.printLatency(bs, (sha_t, lzwc_t, lzwd_t, raid_t))
        r.printLatency(1, (sha_c, lzwc_c, lzwd_c, raid_c))
