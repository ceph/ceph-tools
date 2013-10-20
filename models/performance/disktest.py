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
disk simulation exerciser
   prints out all of the interesting disk performance
   parameters and simulated bandwidth for standard tests
"""

from units import *
from Report import Report
import SimDisk


def tptest(disk, filesize, depth=1, bsizes=(4096, 128 * 1024, 4096 * 1024)):
    """
    run a standard set of throughputs against a specified device
        disk -- device to be tested
        filesize -- size of the file used for the test
        depth -- number of queued parallel operations
    """
    r = Report(("seq read", "seq write", "rnd read", "rnd write"))
    r.printHeading()
    for bs in bsizes:
        tsr = disk.avgTime(bs, filesize, read=True, seq=True, depth=depth)
        tsw = disk.avgTime(bs, filesize, read=False, seq=True, depth=depth)
        trr = disk.avgTime(bs, filesize, read=True, seq=False, depth=depth)
        trw = disk.avgTime(bs, filesize, read=False, seq=False, depth=depth)

        # compute the corresponding bandwidths
        bsr = bs * SECOND / tsr
        bsw = bs * SECOND / tsw
        brr = bs * SECOND / trr
        brw = bs * SECOND / trw

        r.printBW(bs, (bsr, bsw, brr, brw))
        r.printIOPS(bs, (bsr, bsw, brr, brw))
        r.printLatency(bs, (tsr, tsw, trr, trw))


def disktest(disk):
    """ compute & display basic performance data for a simulated disk
        disk -- device to be tested
    """

    print("    basic disk parameters:")
    print("\tdrive size\t%d GB" % gig(disk.size))
    print("\trpm       \t%d" % disk.rpm)
    print("\txfer rate \t%d MB/s" % meg(disk.media_speed))
    print("\tseek time \t%d-%dus, avg %dus" %
          (disk.settle_read, disk.max_seek, disk.avg_seek))
    print("\twrite back\t%s" % ("True" if disk.do_writeback else "False"))
    print("\tread ahead\t%s" % ("True" if disk.do_readahead else "False"))
    print("\tmax depth \t%d" % disk.nr_requests)

    print("\n    computed performance parameters:")
    rot = 0 if disk.rpm == 0 else (MEG / (disk.rpm / 60))
    print("\trotation   \t%dus" % (rot))
    print("\ttrack size \t%d bytes" % disk.trk_size)
    print("\theads      \t%d" % disk.heads)
    print("\tcylinders  \t%d" % disk.cylinders)

    print("\n    data transfer times:")
    print("\t   size      time      iops")
    for bs in (4096, 128 * 1024, 4096 * 1024):
        t = disk.xferTime(bs)
        r = 1000000 / t
        print("\t%6dK  %7dus  %7d" % (kb(bs), t, r))

    print("\n    seek times:")
    print("\t  cyls      read      write")
    cyls = 1
    while cyls < disk.cylinders * 10:
        print("\t%7d  %7dus  %7dus" %
              (cyls, disk.seekTime(cyls), disk.seekTime(cyls, read=False)))
        cyls *= 10

#
# basic unit test exerciser
#
if __name__ == '__main__':
    for t in ["disk", "ssd"]:
        if t == "disk":
            disk = SimDisk.Disk(size=2000 * GIG)
        else:
            disk = SimDisk.SSD(size=20 * GIG)

        print("\nDefault %s simulation" % (t))
        disktest(disk)
        for depth in [1, 32]:
            print("")
            print("    Estimated Throughput (depth=%d)" % depth)
            tptest(disk, filesize=16 * GIG, depth=depth)
