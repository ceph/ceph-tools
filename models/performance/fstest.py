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

from units import *


"""
file system simulation exerciser
"""


def fstest(fs, filesize=16 * MEG, depth=1, direct=False,
            sync=False, crtdlt=False):
    """ compute & display standard fio to filesystem on a disk
        fs -- file system to be tested
        filesize -- size of file in which I/O is being done
        depth -- number of concurrent requests
        direct -- I/O is direct (not buffered)
        sync -- updates are immediately flushed
    """

    if crtdlt:
        tc = fs.create(sync=sync)
        td = fs.delete(sync=sync)
        print("\t\t     create\t      delete")
        print("\t\t%6d IOPS\t %6d IOPS" % (iops(tc), iops(td)))
        print("")

    print("\t    bs\t    seq read\t   seq write\t   rnd read\t   rnd write")
    print("\t -----\t    --------\t   ---------\t   --------\t   ---------")
    for bs in (4096, 128 * 1024, 4096 * 1024):
        tsr = fs.read(bs, filesize, seq=True, depth=depth, direct=direct)
        tsw = fs.write(bs, filesize, seq=True, depth=depth, direct=direct,
                    sync=sync)
        trr = fs.read(bs, filesize, seq=False, depth=depth, direct=direct)
        trw = fs.write(bs, filesize, seq=False, depth=depth, direct=direct,
                    sync=sync)

        if bw(bs, tsw) >= 10:
            format = "\t%5dK\t%7d MB/s\t%7d MB/s\t%7.1f MB/s\t%7.1f MB/s"
        else:
            format = "\t%5dK\t%7.1f MB/s\t%7.1f MB/s\t%7.1f MB/s\t%7.1f MB/s"
        print(format %
                (kb(bs), bw(bs, tsr), bw(bs, tsw),
                 bw(bs, float(trr)), bw(bs, float(trw))))
        print("\t    \t %6d IOPS\t %6d IOPS\t %6d IOPS\t %6d IOPS" %
                (iops(tsr), iops(tsw), iops(trr), iops(trw)))
