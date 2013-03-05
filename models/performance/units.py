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
commonly used units and functions to convert between them
"""

# mnemonic scale constants
MEG = 1000 * 1000
GIG = MEG * 1000

KB = 1024
MB = KB * 1024
GB = MB * 1024


# unit conversion functions
def kb(val):
    """ number of kilobytes (1024) in a block """
    return val / KB


def meg(val):
    """ mumber of millions (10^6) of bytes """
    return val / MEG


def gig(val):
    """ mumber of billions (10^9) of bytes """
    return val / GIG


def iops(us):
    """ convert a us/operation into IOPS """
    return MEG / us


def bw(bs, us):
    """ convert block size and us/operation into MB/s bandwidth """
    return bs / us
