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
This performance simulator returns results based on supplied
data (rather than lower level simulations).
"""

from units import *


def interpolate(x1, y1, x2, y2, v):
    """ linear interpolation """
    return y1 + ((y2 - y1) * (v - x1) / x2)


def log2(x):
    """ log base 2 """
    l = 0
    while x > 1:
        l += 1
        x /= 2
    return l


def interp2(x1, y1, x2, y2, v):
    """ exponential interpolation """
    return interpolate(log2(x1), y1, log2(x2), y2, log2(v))


class DataFS:

    def __init__(self, dict, desc="Data Described", size=2 * TERA):
        """ create a simulation based on the specified dict """
        self.desc = desc
        self.dict = dict
        self.size = size
        self.speed = 140 * MEG      # assumed transfer speed

    def time(self, op, seq, bsize, depth):
        """
            use supplied data to estimate time to perform an operation
            op -- 'read' or 'write'
            seq -- sequential (vs Random)
            bsize -- bytes per transfer
            depth -- number of concurrent transfers
        """

        # choose sequential or random
        s = "seq" if seq else "rand"

        # decide which throughput number to use
        if bsize <= 32 * 1024:
            bs = "4k"
            delta = 4096 - bsize
        elif bsize <= 1024 * 1024:
            bs = "128k"
            delta = (128 * 1024) - bsize
        else:
            bs = "4m"
            delta = (4096 * 1024) - bsize
        key = "%s-%s-%s-d" % (s, op, bs)

        # we may have to interporate the effects of queue depth
        if depth > 1 and depth < 32:
            bw1 = self.dict[key + "1"]
            bw32 = self.dict[key + "32"]
            bw = interp2(1, bw1, 32, bw32, depth)
        else:
            bw = self.dict["%s%d" % (key, depth)]

        # figure out the implied us for this operation
        us = MEG * bsize / bw           # convert bw to us
        us += MEG * delta / self.speed  # adjust for nonstd bsize
        return us

    def read(self, bsize, file_size=-1, seq=True, depth=1, direct=False):
        """ average time for reads from a single file
            bsize -- read unit (bytes)
            file_size -- size of file being read from (bytes)
            seq -- sequential (vs random) read
            depth -- number of queued operations
        """
        # assume the file size is large enough that we can ignore hits
        assert direct == False    # not used for filestore simulation
        return self.time("read", seq, bsize, depth)

    def write(self, bsize, file_size=-1,
                seq=True, depth=1, direct=False, sync=False):
        """ average time for writes to a single file
            bsize -- read unit (bytes)
            file_size -- size of file being read from (bytes)
            seq -- sequential (vs random) read
            depth -- number of queued operations
            direct -- don't go through the buffer cache
            sync -- force flush after write
        """
        # assume the file size is large enough that we can ignore hits
        assert direct == False  # not used for filestore simulation

        if sync:
            # we didn't measure this, so guess and hope
            t = self.time("write", False, bsize, 1)     # +1 metadata write
            t += self.time("write", seq, bsize, 1)      # no depth benefits
        else:
            t = self.time("write", seq, bsize, depth)
        return t

    def create(self):
        """ average time for a file creation """
        return MEG / self.dict['create']

    def delete(self):
        """ average time for a file deletion """
        return MEG / self.dict['delete']


if __name__ == '__main__':
    """
        Unit test ... instantiate a file system and run an fstest
    """
    testDict = {
        'seq-read-4k-d1': 52 * MEG,
        'seq-write-4k-d1': 45 * MEG,
        'rand-read-4k-d1': 0.6 * MEG,
        'rand-write-4k-d1': 1.5 * MEG,
        'seq-read-4k-d32': 109 * MEG,
        'seq-write-4k-d32': 44 * MEG,
        'rand-read-4k-d32': 2.0 * MEG,
        'rand-write-4k-d32': 1.5 * MEG,

        'seq-read-128k-d1': 129 * MEG,
        'seq-write-128k-d1': 126 * MEG,
        'rand-read-128k-d1': 17.1 * MEG,
        'rand-write-128k-d1': 34.9 * MEG,
        'seq-read-128k-d32': 131 * MEG,
        'seq-write-128k-d32': 126 * MEG,
        'rand-read-128k-d32': 43.8 * MEG,
        'rand-write-128k-d32': 34.9 * MEG,

        'seq-read-4m-d1': 117 * MEG,
        'seq-write-4m-d1': 116 * MEG,
        'rand-read-4m-d1': 99 * MEG,
        'rand-write-4m-d1': 103.4 * MEG,
        'seq-read-4m-d32': 117 * MEG,
        'seq-write-4m-d32': 116 * MEG,
        'rand-read-4m-d32': 99 * MEG,
        'rand-write-4m-d32': 103.4 * MEG,

        'create': 1000,
        'delete': 2000
    }

    import fstest
    from FileStore import FileStore
    import filestoretest

    data = DataFS(testDict, desc="sampled XFS")
    for d in (1, 2, 4, 8, 16, 32):
        print("\n%s Filesystem, depth=%d" % (data.desc, d))
        fstest.fstest(data, depth=d)

    fstore = FileStore(data, None, journal_share=1)
    for d in (1, 32):
        print("\nFilestore in %s Filesystem, depth=%d" % (data.desc, d))
        filestoretest.fstoretest(fstore, depth=d)
