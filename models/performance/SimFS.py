#
# This is intended to be able to simulate the overhead a file
# system adds to standard I/O test patterns
#

import math


def interpolate(points, value):
    """ compute a point on a linear function """

    # figure out the line passing between these points
    (first, last) = sorted(points.keys())
    slope = float(points[last] - points[first]) / (last - first)
    intercept = float(points[first]) - (slope * first)

    # interpolate/extrapolate our position
    return intercept + (slope * value)


class FS:
    """ Performance Modeling File System Simulation. """

    # metadata block size and location
    md_seek = 0.5       # distance from data to metadata
    md_size = 4096      # size of a metadata update block

    # number of metatdata operations assocaited with common ops
    #   defaults based on 4K blocks, 1K pointers per indirect
    max_shard = 4096                # 4K blocks
    md_read = {4096: .001, \
                4096 * 1024: 1.0}   # 1K pointers per block
    md_write = {4096: .001, \
                4096 * 1024: 2.0}   # 1K pointers + reference
    seq_bonus = {4096: 0.001, \
                4096 * 1024: 0.001}  # 1K pointers per block

    sync_time = 1000000         # default flush interval (us)
    md_create = 3.0             # parent directory, directory inode, new inode
    md_delete = 2.0             # parent directory, deleted inode

    def __init__(self, disk):
        """ create a file system simulation """

        self.disk = disk

    def read(self, bsize, file_size, seq=True, depth=1):
        """ average time for file reads """

        # FS may not support specified bsize
        if bsize > self.max_shard:
            shards = bsize / self.max_shard
            bsize = self.max_shard
        else:
            shards = 1

        # figure out the times for the underlying disk operations
        time = self.disk.avgTime(bsize, file_size, True, seq, depth)
        if seq or shards == 1:
            time *= shards
        else:
            time += (shards - 1) * self.disk.avgTime(bsize, file_size, \
                True, seq=True, depth=depth)

        # MAYBE: there should be a depth correction to MD reads
        index_seek = \
            self.disk.seekTime(self.disk.cylinders * self.md_seek)
        index_latency = \
            self.disk.latency(self.md_size, read=True, seq=False)
        index_xfer = self.disk.xferTime(self.md_size, read=True)

        # figure out how many metadata reads we'll have to do
        mdreads = shards * interpolate(self.md_read, bsize)
        if seq:
            # MAYBE: apply the sequential bonus to sharded reads?
            mdreads *= interpolate(self.seq_bonus, bsize)
        time += mdreads * (index_seek + index_latency + index_xfer)

        return time

    def write(self, bsize, file_size, seq=True, depth=1, sync=False):
        """ average time for file writes """

        # FS may not support specified bsize
        if bsize > self.max_shard:
            shards = bsize / self.max_shard
            bsize = self.max_shard
        else:
            shards = 1

        # figure out the times for the underlying disk operations
        time = self.disk.avgTime(bsize, file_size, False, seq, depth)
        if seq or shards == 1:
            time *= shards
        else:
            time += (shards - 1) * self.disk.avgTime(bsize, file_size, \
                False, seq=True, depth=depth)

        # MAYBE: there should be a nosync/depth correction to MD updates
        index_seek = \
            self.disk.seekTime(self.disk.cylinders * self.md_seek)
        index_latency = \
            self.disk.latency(self.md_size, read=False, seq=False)
        index_xfer = self.disk.xferTime(self.md_size, read=False)

        # figure out how many metadata writes we'll have to do
        mdwrites = shards * interpolate(self.md_write, bsize)
        if seq:
            # MAYBE: apply the sequential bonus to sharded writes?
            mdwrites *= interpolate(self.seq_bonus, bsize)

        # also consider the I-node updates
        if sync:
            mdwrites += 1
        else:
            mdwrites += time / self.sync_time

        time += mdwrites * (index_seek + index_latency + index_xfer)

        return time

   # FIX: implement create
   # FIX: implement delete


class btrfs(FS):
    """ BTRFS simulation """

    def __init__(self, disk, age=0):
        """ Instantiate a BTRFS simulation. """
        # curve fitting at its ignorant worst

        FS.__init__(self, disk)

        # clean BTRFS calibration values
        self.sync_time = 100000
        self.max_shard = 4096 * 1024
        self.md_read = {4096: .10, 4096 * 1024: 0.45}
        self.md_write = {4096: .11, 4096 * 1024: 0.30}
        self.seq_bonus = {4096: 0.0001, 4096 * 1024: 0.001}

        # use the age to (very badly) simulate fragementation
        if age > 0:
            self.md_read[4096] *= 1 + (30 * age)
            self.md_write[4096] *= 1
            self.md_read[4096 * 1024] *= 1 + (1 * age)
            self.md_write[4096 * 1024] *= 1 + (70 * age)
            self.seq_bonus[4096] *= 1 + (50 * age)
            self.seq_bonus[4096 * 1024] *= 1 + (7000 * age)

            shifts = age / .2
            while shifts > 0:
                self.max_shard /= 2
                shifts -= 1


class xfs(FS):
    """ XFS simulation """

    def __init__(self, disk, age=0):
        """ Instantiate a XFS simulation. """
        # curve fitting at its ignorant worst

        FS.__init__(self, disk)

        # need XFS calibration values !!!
        self.sync_time = 100000
        self.max_shard = 4096 * 1024
        self.md_read = {4096: .10, 4096 * 1024: 0.45}
        self.md_write = {4096: .11, 4096 * 1024: 0.30}
        self.seq_bonus = {4096: 0.0001, 4096 * 1024: 0.001}


class ext4(FS):
    """ EXT4 simulation """

    def __init__(self, disk, age=0):
        """ Instantiate a EXT4 simulation. """
        # curve fitting at its ignorant worst

        FS.__init__(self, disk)

        # need EXT4 calibration values !!!
        self.sync_time = 100000
        self.max_shard = 4096 * 1024
        self.md_read = {4096: .10, 4096 * 1024: 0.45}
        self.md_write = {4096: .11, 4096 * 1024: 0.30}
        self.seq_bonus = {4096: 0.0001, 4096 * 1024: 0.001}
