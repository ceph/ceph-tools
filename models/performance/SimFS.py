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
This is intended to be able to simulate the performance of
a specified file system for a few basic types of I/O.
Rather than attempt a (prohibitively difficult) low
level simulation, it simply attempts to model the overheads
that a file system imposes on various operations.

Simple models of complex things are (IMHO) fundamentally
star-crossed, but all we need is an approximate modeling
of the average costs of a few things:
   O_DIRECT fio tests (seq/random) with variable size and depth
   filestore data and journal reads and writes
"""

from units import SECOND, MEG


def log2(v):
    """ log base 2 """
    l = 0
    while v > 1:
        l += 1
        v /= 2
    return l


#
# these functions get used all the time to estimate the meta-data
# overhead associated with various operations, which we model as
# afine-linear functions
#
def interpolate(points, x):
    """ interpolate a point on a linear function
        points -- map containing two <size,value> points
        x -- X value for which function is to be computed
    """

    # figure out the line passing between these points
    (first, last) = sorted(points.keys())
    dy = float(points[last] - points[first])
    dx = last - first
    intercept = float(points[first]) - (first * dy / dx)

    # interpolate/extrapolate our position
    y = intercept + (x * dy / dx)
    return y


def interpolate2(points, v):
    """ interpolate a point on a logarithmic function
        points -- map containing two <size,value> points
        v -- X value for which function is to be computed
    """

    # figure out the line passing between these points
    (first, last) = sorted(points.keys())
    dy = float(points[last] - points[first])
    dx = log2(last) - log2(first)
    intercept = float(points[first]) - (log2(first) * dy / dx)

    # interpolate/extrapolate our position
    x = log2(v)
    y = intercept + (x * dy / dx)
    return y


class FS:
    """ Performance Modeling File System Simulation. """
    # these parameters are very interesting, but their default
    # values are boring, being over-ridden by per-FS constructors

    # ACTIVE INGREDIENTS IN MODEL:
    #   We model the cost of file system meta-data access as
    #   an overhead per data access (number of meta-data read/write
    #   operations per data read/write operation.  These overheads
    #   are modeled as an afine-linear function of the log2 of the
    #   block size, defined by two points:
    #       md_read ..... # meta data reads per block read
    #       md_write .... # meta data writes per block write
    #   for sequential I/O, most of these are in cache
    #       seq_read .... # fraction of MD refs requiring reads
    #       seq_write ... # fraction of MD upates requiring writes
    #   for direct I/O, fs may limit allowable parallelism
    #
    md_read = {4096: .001, 4096 * 1024: 1.0}
    md_write = {4096: .001, 4096 * 1024: 2.0}
    seq_read = {4096: 0.001, 4096 * 1024: 0.001}
    seq_write = {4096: 0.001, 4096 * 1024: 0.001}
    max_dir_r = {4096: 32, 4096 * 1024: 32}
    max_dir_w = {4096: 32, 4096 * 1024: 32}

    # FIX ... all these CPU cost numbers are bogus
    # CPU costs for common operations in us (/MB)
    cpu_read = {4096: 12, 4096 * 1024: 125}
    cpu_write = {4096: 250, 4096 * 1024: 250}
    cpu_open = 75       # CPU time (us)
    cpu_create = 100    # CPU time (us)
    cpu_delete = 30     # CPU time (us)
    cpu_getatr = 10     # CPU time (us)
    cpu_setatr = 20     # CPU time (us)

    # other important modeling parameters (boring default values)
    md_size = 4096              # size of a metadata update block
    max_shard = 4096            # largest contiguous allocation unit
    seq_shard = False           # allocated shards are nearly contiguous
    flush_bytes = 100000000     # flush cache after this many bytes written
    flush_time = 500000         # flush cache after this much time elapses
    flush_max = 128             # max parallelism for cache flush writes
    md_seek = 0                 # average cylinders from data to metadata

    # number of metadata writes associated with create/delete
    md_open = 1.0               # one directory read (rest in cache)
    md_create = 3.0             # parent directory, directory inode, new inode
    md_delete = 2.0             # parent directory, deleted inode

    # this is boring, look at the per FS constructors
    def __init__(self, disk, md_span, cpu=None):
        """ create a file system simulation w/default parms
            disk -- disk simulation upon which we are implemented
            md_span -- fraction of disk for data/metadata seeks
        """

        self.desc = "BSD"
        self.disk = disk
        self.size = disk.size
        self.cpu = cpu
        self.md_seek = md_span * self.size

        # FIX better values for cpu_* parameters, computed w/CPU

    def flush_depth(self, bsize, time):
        """ write depth resulting from cache flushes
            bsize -- bytes written per operation
            time -- micro-seconds of I/O per operation
        """

        # how many writes accumulate between syncs
        d = self.flush_time / time

        # is this write so large as to force its own flush
        if bsize > 0 and self.flush_bytes > bsize * d:
            d = self.flush_bytes / bsize

        # but this is subject to a maximum FS flush rate
        if d < 1:
            return 1
        elif d < self.flush_max:
            return d
        else:
            return self.flush_max

    #
    # This function is intended to model the fio tests we use to
    # measure disk/file system performance, and the I/O patterns
    # used by the filestore to write the journal and read/write
    # data disks
    #
    def read(self, bsize, file_size, seq=True, depth=1, direct=False):
        """ average time for reads from a single file
            bsize -- read unit (bytes)
            file_size -- size of file being read from (bytes)
            seq -- sequential (vs random) read
            depth -- number of queued operations
        """

        # see if we have to break this up into smaller requests
        if bsize > self.max_shard:
            shards = bsize / self.max_shard
            bsize = self.max_shard
        else:
            shards = 1

        # estimate effective parallelism the disk will see
        d = depth * shards
        if direct:
            m = interpolate(self.max_dir_r, bsize)
            if d > m:
                d = m

        # figure out the times for the underlying disk operations
        #  (initial read is seq per op, shard reads are seq per fs)
        time = self.disk.avgRead(bsize, file_size, seq=seq, depth=d)
        if seq or shards == 1:
            time *= shards
        else:
            time += (shards - 1) * \
                self.disk.avgRead(bsize,
                                  file_size, seq=self.seq_shard,
                                  depth=d)

        # add in the time for the meta-data lookups
        # FIX: shards multiplier should get the seq read bonus
        mdreads = shards * interpolate(self.md_read, bsize)
        if seq:
            mdreads *= interpolate(self.seq_read, bsize)
        time += mdreads * \
            self.disk.avgRead(self.md_size, self.md_seek, depth=d)

        bw = bsize * SECOND / time

        loads = {}
        loads['disk'] = 1.0
        loads['cpu'] = interpolate(self.cpu_read, bsize) / SECOND

        return (time, bw, loads)

    #
    # This function is intended to model the fio tests we use to
    # measure disk/file system performance, and the I/O patterns
    # used by the filestore to write the journal and read/write
    # data disks
    #
    def write(self, bsize, file_size, seq=True, depth=1,
              direct=False, sync=False):
        """ average time for writes to a single file
            bsize -- read unit (bytes)
            file_size -- size of file being read from (bytes)
            seq -- sequential (vs random) read
            depth -- number of queued operations
            direct -- don't go through the buffer cache
            sync -- force flush after write
        """

        # FS may not support specified bsize
        if bsize > self.max_shard:
            shards = bsize / self.max_shard
            bsize = self.max_shard
        else:
            shards = 1

        # estimate effective parallelism the disk will see
        d = depth * shards
        if not sync and not direct:
            t = shards * self.disk.avgWrite(bsize, file_size, seq, d)
            d = self.flush_depth(bsize * shards, t)
        elif direct:
            m = interpolate(self.max_dir_w, bsize)
            if d > m:
                d = m

        # figure out the times for the underlying disk operations
        #  (initial write is seq per op, shard writes are seq per fs)
        time = self.disk.avgWrite(bsize, file_size, seq=seq, depth=d)
        if seq or shards == 1:
            time *= shards
        else:
            time += (shards - 1) * self.disk.avgWrite(bsize, file_size,
                                                      seq=self.seq_shard,
                                                      depth=d)

        # figure out how many metadata writes we'll have to do
        mdw = shards * interpolate(self.md_write, bsize)
        if seq:
            # MAYBE: apply the sequential bonus to sharded writes?
            mdw *= interpolate(self.seq_write, bsize)

        # also consider the time for the meta-data updates
        if sync:
            mdw += 1    # I-node updates don't come along for free
            d = 1       # we don't parallelize requests
        t = mdw * self.disk.avgWrite(self.md_size, self.md_seek, depth=d)
        time += t
        bw = bsize * SECOND / time

        loads = {}
        loads['disk'] = 1.0  # by design
        loads['cpu'] = interpolate(self.cpu_write, bsize) / SECOND

        return (time, bw, loads)

    def stat(self):
        """ stat a file whose parent directory is already in cache """
        t = self.disk.avgRead(self.md_size, self.md_seek)
        time = self.md_open * t
        bw = SECOND / time

        loads = {}
        loads['disk'] = 1.0
        loads['cpu'] = float(self.cpu_open) / SECOND
        return (time, bw, loads)

    def open(self):
        """ open a file whose parent directory is already in cache """
        t = self.disk.avgRead(self.md_size, self.md_seek)
        time = self.md_open * t
        bw = SECOND / time

        loads = {}
        loads['disk'] = 1.0
        loads['cpu'] = float(self.cpu_open) / SECOND
        return (time, bw, loads)

    def create(self, sync=False):
        """ new file creation """

        t = self.disk.avgWrite(self.md_size, self.md_seek)
        if not sync:
            d = self.flush_depth(self.md_size, t)
            t = self.disk.avgWrite(self.md_size, self.md_seek, depth=d)
        time = self.md_create * t
        bw = SECOND / time

        loads = {}
        loads['disk'] = 1.0
        loads['cpu'] = float(self.cpu_create) / SECOND
        return (time, bw, loads)

    def delete(self, sync=False):
        """ file deletion """

        t = self.disk.avgWrite(self.md_size, self.md_seek)
        if not sync:
            d = self.flush_depth(self.md_size, t)
            t = self.disk.avgWrite(self.md_size, self.md_seek, depth=d)
        time = self.md_delete * t
        bw = SECOND / time

        loads = {}
        loads['disk'] = 1.0
        loads['cpu'] = float(self.cpu_delete) / SECOND

        return (time, bw, loads)

    def getattr(self):
        """ get file attributes for an open file """

        # FIX shouldn't this be in memory cheap
        time = self.disk.avgRead(self.md_size, self.md_seek)
        bw = SECOND / time

        loads = {}
        loads['disk'] = 1.0
        loads['cpu'] = float(self.cpu_getatr) / SECOND
        return (time, bw, loads)

    def setattr(self, sync=False):
        """ set file attributes for an open file """

        time = self.disk.avgWrite(self.md_size, self.md_seek)
        if not sync:
            d = self.flush_depth(self.md_size, time)
            time = self.disk.avgWrite(self.md_size, self.md_seek, depth=d)
        bw = SECOND / time

        loads = {}
        loads['disk'] = 1.0
        loads['cpu'] = float(self.cpu_setatr) / SECOND

        return (time, bw, loads)


# BTRFS calibration values based on Dec'12 customer results
class btrfs(FS):
    """ BTRFS simulation """

    def __init__(self, disk, age=0, cpu=None):
        """ Instantiate a BTRFS simulation. """
        # curve fitting at its ignorant worst

        FS.__init__(self, disk, cpu=cpu, md_span=0.5)
        self.desc = "BTRFS"
        if age > 0:
            self.desc += "(%3.1f)" % age

        # clean BTRFS calibration values
        self.flush_time = 100000
        self.max_shard = 4096 * 1024
        self.md_read = {4096: .10, 4096 * 1024: 0.45}
        self.md_write = {4096: .11, 4096 * 1024: 0.30}
        self.seq_read = {4096: 0.0001, 4096 * 1024: 0.001}
        self.seq_write = {4096: 0.0001, 4096 * 1024: 0.001}

        # use the age to (very badly) simulate fragementation
        if age > 0:
            self.md_read[4096] *= 1 + (30 * age)
            self.md_write[4096] *= 1
            self.md_read[4096 * 1024] *= 1 + (1 * age)
            self.md_write[4096 * 1024] *= 1 + (70 * age)
            self.seq_read[4096] *= 1 + (50 * age)
            self.seq_write[4096] *= 1 + (50 * age)
            self.seq_read[4096 * 1024] *= 1 + (7000 * age)
            self.seq_write[4096 * 1024] *= 1 + (7000 * age)

            shifts = age / .2
            while shifts > 0:
                self.max_shard /= 2
                shifts -= 1


# XFS calibration values based on Jan'13 customer results
class xfs(FS):
    """ XFS simulation """

    def __init__(self, disk, age=0, cpu=None):
        """ Instantiate a XFS simulation. """

        FS.__init__(self, disk, cpu=cpu, md_span=0.5)
        self.desc = "XFS"
        if age > 0:
            self.desc += "(%3.1f)" % age

        self.max_shard = 4096 * 1024
        self.seq_shard = False
        self.flush_max = 16
        self.md_read = {4096: 0.08, 4096 * 1024: 1.05}
        self.md_write = {4096: 0.05, 4096 * 1024: 1.30}
        self.seq_read = {4096: 0.012, 4096 * 1024: 0.40}
        self.seq_write = {4096: 0.095, 4096 * 1024: 0.60}
        self.max_dir_r = {4096: 32, 4096 * 1024: 1}
        self.max_dir_w = {4096: 1, 4096 * 1024: 1}


def makefs(disk, dict):
    """ instantiate the filesystem described by a configuration dict
        disk -- on which file system is to be created
        dict -- of file system paramters
             -- fs: type of file system
             -- age: 0-1
    """

    age = dict['age'] if 'age' in dict else 0

    if 'fs' in dict and dict['fs'] == 'btrfs':
        return btrfs(disk, age)
    elif 'fs' in dict and dict['fs'] == 'ext4':
        return ext4(disk, age)
    elif 'fs' in dict and dict['fs'] == 'xfs':
        return xfs(disk, age)
    elif 'fs' in dict and dict['fs'] == 'zfs':
        from zfs import zfs
        return zfs(disk, age)
    else:
        return xfs(disk, age)


from Report import Report


def fstest(fs, dict, descr=""):
    """
    exercise a file system with tests described in a dict
        fs -- device to be tested
        dict --
            FCrtDlt ... do create/deletes as well
            FioFsize ... size of test file
            FioFdepth ... list of request depths
            FioFbs ... list of block sizes
            FioFsync ... synchronous writes
            FioFdir ... O_DIRECT
    """

    dflt = {        # default throughput test parameters
        'FioFsize': 16 * MEG,
        'FioFdepth': [1, 32],
        'FioFbs': [4096, 128 * 1024, 4096 * 1024],
        'FioFsync': False,
        'FioFdir': True,
        'Fmisc': True,
    }

    sz = dict['FioFsize'] if 'FioFsize' in dict else dflt['FioFsize']
    depths = dict['FioFdepth'] if 'FioFdepth' in dict else dflt['FioFdepth']
    bsizes = dict['FioFbs'] if 'FioFbs' in dict else dflt['FioFbs']
    sync = dict['FioFsync'] if 'FioFsync' in dict else dflt['FioFsync']
    direct = dict['FioFdir'] if 'FioFdir' in dict else dflt['FioFdir']
    misc = dict['Fmisc'] if 'Fmisc' in dict else dflt['Fmisc']

    if misc:
        print("Basic operations to %s" % (descr))
        r = Report(("create", "open", "setattr", "delete"))
        (tc, bwc, loadc) = fs.create(sync=sync)
        (to, bwo, loado) = fs.open()
        (ts, bws, loads) = fs.setattr(sync=sync)
        (td, bwd, loadd) = fs.delete(sync=sync)

        r.printHeading()
        r.printIOPS(1, (bwc, bwo, bws, bwd))
        r.printLatency(1, (tc, to, ts, td))
        print("")

    for d in depths:
        print("FIO (%s) to %s, depth=%d" %
              ("direct" if direct else "buffered", descr, d))
        r = Report(("seq read", "seq write", "rnd read", "rnd write"))
        r.printHeading()
        for bs in bsizes:
            (tsr, bsr, lsr) = fs.read(bs, sz, seq=True, depth=d,
                                      direct=direct)
            isr = SECOND / tsr
            (tsw, bsw, lsw) = fs.write(bs, sz, seq=True, depth=d,
                                       direct=direct, sync=sync)
            isw = SECOND / tsw
            (trr, brr, lrr) = fs.read(bs, sz, seq=False, depth=d,
                                      direct=direct)
            irr = SECOND / trr
            (trw, brw, lrw) = fs.write(bs, sz, seq=False, depth=d,
                                       direct=direct, sync=sync)
            irw = SECOND / trw

            r.printBW(bs, (bsr, bsw, brr, brw))
            r.printIOPS(0, (isr, isw, irr, irw))
            r.printLatency(0, (tsr, tsw, trr, trw))
        print("")


#
# run a standard test series
#
if __name__ == '__main__':

        from SimDisk import makedisk
        disk = makedisk({'device': 'disk'})

        for f in ('btrfs', 'xfs', 'zfs'):
            fs = makefs(disk, {'fs': f})
            fstest(fs, {}, descr="%s on %s" % (fs.desc, fs.disk.desc))
