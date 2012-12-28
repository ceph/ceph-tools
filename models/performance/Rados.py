#
# This is intended to be able to simulate the overhead that
# a remote RADOS client experiences for standard test loads
#

import math

SECOND = 1000000
GIG    = 1000000000

class Rados:
    """ Performance Modeling RADOS Simulation. """

    nic_overhead = 0.25		# fraction of NIC we can't use

    def __init__(self, filestore, nic_bw=10 * GIG, nodes=1, osd_per_node=1):
        """ create a RADOS simulation """

        self.filestore = filestore
        self.bw = (1 - self.nic_overhead) * (nic_bw / 8)
        self.num_nodes = nodes
        self.num_osds = nodes * osd_per_node

    def read(self, bsize, obj_size, depth=1):
        """ average time for reads """

        # figure out the effective parallelism
        p = min(depth, self.num_osds)		# parallel requests
        d = max(1, depth / self.num_osds)	# requests per OSD

        # figure out the filestore and network times
        ftime = self.filestore.read(bsize, obj_size, depth=d)
        ntime = SECOND * bsize / self.bw

        return (ftime + ntime) / p

    def write(self, bsize, obj_size, depth=1, copies=1):
        """ average time for object writes """

        # figure out the effective parallelism
        p = min(depth, self.num_osds)		# parallel requests
        d = max(1, depth / self.num_osds)	# requests per OSD

        # time for the remote filestores to do the writes
        ftime = self.filestore.write(bsize, obj_size, depth=d)

        # network time must also account for replication
        ntime = SECOND * bsize / self.bw
        if copies > 1:
            ntime *= copies - 1

        # we may be limited by either disk or network throughput
        return max(ftime, ntime) / p

    def create(self, depth=1):
        """ new object creation """

        p = min(depth, self.num_osds)		# parallel requests
        return self.filestore.create() / p

    def delete(self, depth=1):
        """ object deletion """

        p = min(depth, self.num_osds)		# parallel requests
        return self.filestore.delete() / p

