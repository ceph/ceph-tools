#
# This is intended to be able to simulate the overhead a file
# system adds to standard I/O test patterns
#

import math


class SimFS:
    """ Performance Modeling File System Simulation. """

    # basic file system performance parameters
    inode_sep = 0.9     # distance from data to inode blocks
    index_sep = 0.1     # distance from data to index blocks
    max_extent = 32 * 1024    # largest variable extent
    sync_time = 1000000     # inode update interval (us)
    pointer_length = 8

    def __init__(self, disk, extent_size=4096):
        """ create a file system simulation """

        self.disk = disk
        self.extent = extent_size

    # this is the primary method for simulating an I/O scenario
    def avgTime(self, bsize, file_size, read=True, seq=True,
        depth=1, sync=False):
        """ average operation time (us) for a specified test. """

        # figure out the underlying disk I/O
        time = self.disk.avgTime(bsize, file_size, read, seq, depth)

        # figure out how many extents this operation involves
        num_ptr = self.extent / self.pointer_length
        if self.max_extent > self.extent:
            if bsize < self.max_extent:
                num_extents = 1
            else:
                num_extents = float(bsize) / self.max_extent
        else:
            num_extents = float(bsize) / self.extent

        # how long does it take to consult/update the index
        num_xblocks = num_extents / num_ptr
        inode_seek = \
            self.disk.seekTime(self.disk.cylinders * self.inode_sep)
        index_seek = \
            self.disk.seekTime(self.disk.cylinders * self.index_sep)
        index_latency = \
            self.disk.latency(self.extent, read=read, seq=False, depth=1)
        index_xfer = self.disk.xferTime(self.extent, read=read)

        if read:
            if not seq:
                # still have to read index blocks to find our data
                time += num_xblocks * (index_seek + index_latency + index_xfer)
        else:
            # we have to update a bunch of index blocks
            time += num_xblocks * (index_seek + index_latency + index_xfer)

            # and we occasionally have to update an inode
            inode_upd = 1 if sync else time / float(self.sync_time)
            time += inode_upd * (inode_seek + index_latency + index_xfer)

        return time
