#
# This is intended to be able to simulate the overhead a file
# system adds to standard I/O test patterns
#

import math

class SimFS:
    """ Performance Modeling File System Simulation. """

    # basic file system performance parameters
    inode_sep = 0.9
    index_sep = 0.1
    pointer_length = 8

    def __init__(self, disk, extent_size = 4096):
        """ create a file system simulation """

        self.disk = disk
        self.extent = extent_size

    # this is the primary method for simulating an I/O scenario
    def avgTime(self, bsize, file_size, read=True, seq=True, depth=1, sync=False):
        """ average operation time (us) for a specified test. """

        # figure out the underlying disk I/O
        time = self.disk.avgTime(bsize, file_size, read, seq, depth)

        # figure out how many extents this operation involves
        num_ptr = self.extent / self.pointer_length
        num_extents = float(bsize) / self.extent

        if not read:
	    # how many new index blocks will we use in this operation
            num_xblocks = num_extents / num_ptr

            # figure out how lont it takes to update an index block
            index_seek = self.disk.seekTime(self.disk.cylinders * self.index_sep)
            index_latency = self.disk.latency(self.extent, read=False, seq=False, depth=1)
            index_write = self.disk.xferTime(self.extent, read=False)

            if sync:
                # write out new index blocks PLUS the pointers to them
                num_xwrites = 1 + num_xblocks
            else:
		# only write out new index blocks
                num_xwrites = num_xblocks

            time += num_xwrites * (index_seek + index_latency + index_write)

        return time
