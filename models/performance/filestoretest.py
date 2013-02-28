#!/usr/bin/python
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
filestore simulation exerciser
"""

# mnemonic scale constants
MILLION = 1000000    # capacities and speeds

import FileStore


def kb(val):
    """ number of kilobytes (1024) in a block """
    return val / 1024


def iops(us):
    """ convert a us/operation into IOPS """
    return 1000000 / us


def bw(bs, us):
    """ convert block size and us/operation into MB/s bandwidth """
    return bs / us


def fstoretest(fs, obj_size=4 * MILLION, nobj=2500, depth=1, crtdlt=False):
    """ compute & display standard filestore test results """

    if crtdlt:
        tc = fs.create()
        td = fs.delete()
        print("\t\t     create\t      delete")
        print("\t\t%6d IOPS\t %6d IOPS" % (iops(tc), iops(td)))
        print("")

    print("\t    bs\t    rnd read\t   rnd write")
    print("\t -----\t    --------\t   ---------")
    for bs in (4096, 128 * 1024, 4096 * 1024):
        trr = fs.read(bs, obj_size, depth=1, nobj=nobj)
        trw = fs.write(bs, obj_size, depth=depth, nobj=nobj)

        format = "\t%5dK\t%7.1f MB/s\t%7.1f MB/s"
        print(format %
                (kb(bs), bw(bs, float(trr)), bw(bs, float(trw))))
        print("\t    \t %6d IOPS\t %6d IOPS" % (iops(trr), iops(trw)))
