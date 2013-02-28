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
RADOS simulation exerciser
"""

# mnemonic scale constants
MILLION = 1000000   # capacities and speeds
SECOND = 1000000    # times are in micro-seconds

import FileStore


def kb(val):
    """ number of kilobytes (1024) in a block """
    return val / 1024


def iops(us):
    """ convert a us/operation into IOPS """
    return SECOND / us


def bw(bs, us):
    """ convert block size and us/operation into MB/s bandwidth """
    return bs / us


def radostest(fs, obj_size=16 * MILLION, nobj=2500,
            clients=1, depth=1, copies=1, crtdlt=False):
    """ compute & display standard filestore test results """

    if crtdlt:
        tc = fs.create(depth=depth)
        td = fs.delete(depth=depth)
        print("\t\t     create\t      delete")
        print("\t\t%6d IOPS\t %6d IOPS" % (iops(tc), iops(td)))
        print("")

    print("\t    bs\t    rnd read\t   rnd write")
    print("\t -----\t    --------\t   ---------")
    for bs in (4096, 128 * 1024, 4096 * 1024):
        trr = fs.read(bs, obj_size, nobj=nobj, clients=clients, depth=depth)
        trw = fs.write(bs, obj_size, nobj=nobj, depth=depth,
            clients=clients, copies=copies)

        format = "\t%5dK\t%7.1f MB/s\t%7.1f MB/s"
        print(format %
                (kb(bs), bw(bs, float(trr)), bw(bs, float(trw))))
        print("\t    \t %6d IOPS\t %6d IOPS" % (iops(trr), iops(trw)))
