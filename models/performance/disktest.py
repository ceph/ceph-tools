#!/usr/bin/python
#
# disk simulation exerciser
#   prints out all of the interesting disk performance
#   parameters and simulated bandwidth for standard tests

# mnemonic scale constants
MILLION = 1000000    # capacities and speeds

import SimDisk


def kb(val):
    """ number of kilobytes (1024) in a block """
    return val / 1024


def meg(val):
    """ mumber of millions (10^6) of bytes """
    return val / 1000000


def gig(val):
    """ mumber of billions (10^9) of bytes """
    return val / 1000000000


def iops(us):
    """ convert a us/operation into IOPS """
    return 1000000 / us


def bw(bs, us):
    """ convert block size and us/operation into MB/s bandwidth """
    return bs / us


def tptest(disk, filesize, depth):
    print("\t    bs\t    seq read\t   seq write\t   rnd read\t   rnd write")
    print("\t -----\t    --------\t   ---------\t   --------\t   ---------")
    for bs in (4096, 128 * 1024, 4096 * 1024):
        tsr = disk.avgTime(bs, filesize, read=True, seq=True, depth=depth)
        tsw = disk.avgTime(bs, filesize, read=False, seq=True, depth=depth)
        trr = disk.avgTime(bs, filesize, read=True, seq=False, depth=depth)
        trw = disk.avgTime(bs, filesize, read=False, seq=False, depth=depth)

        if bw(bs, tsw) >= 10:
            format = "\t%5dK\t%7d MB/s\t%7d MB/s\t%7.1f MB/s\t%7.1f MB/s"
        else:
            format = "\t%5dK\t%7.1f MB/s\t%7.1f MB/s\t%7.1f MB/s\t%7.1f MB/s"
        print(format % (kb(bs), bw(bs, float(tsr)), bw(bs, float(tsw)),
            bw(bs, float(trr)), bw(bs, float(trw))))
        print("\t    \t%7d IOPS\t%7d IOPS\t%7d IOPS\t%7d IOPS" %
            (iops(tsr), iops(tsw), iops(trr), iops(trw)))


def disktest(disk):
    """ compute & display basic performance data for a simulated disk """

    print("    basic disk parameters:")
    print("\tdrive size\t%d GB" % gig(disk.size))
    print("\trpm       \t%d" % disk.rpm)
    print("\txfer rate \t%d MB/s" % meg(disk.media_speed))
    print("\tseek time \t%d-%dus, avg %dus" %
        (disk.settle_read, disk.max_seek, disk.avg_seek))
    print("\twrite back\t%s" % ("True" if disk.do_writeback else "False"))
    print("\tread ahead\t%s" % ("True" if disk.do_readahead else "False"))
    print("\tmax depth \t%d" % disk.max_depth)

    print("\n    computed performance parameters:")
    rot = 0 if disk.rpm == 0 else (MILLION / (disk.rpm / 60))
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
