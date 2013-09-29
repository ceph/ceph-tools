#
# NO COPYRIGHT/COPYLEFT
#
#   This module defines a sub-class of the Open Source SimFS
#   file system simulation, and as such is an "application"
#   under the Gnu Lesser General Public Licence.  It can be
#   reproduced, modified, and distributed without restriction.
#

"""
    A file system simulation is defined by a collection of
    parameter values that will be interpreted by SimFS.FS

    The suggested process for derving the values for a particular
    file system is by running a set of fio tests (O_DIRECT,
    sequential and random, with block sizes of {4K,128K,4M}
    and depths of {1,4,16,32}, and then tweaking parameters
    to curve-fit the results:

        start with default values + max_shard = 4M
        tweak md_read/write to get d=1 random 4K
        tweak md_read/write to get d=1 random 4M
        tweak md_seq_read/write to get seq 4K
        tweak md_seq_read/write to get seq 4M

        if depth is too effective on direct, consider tweaking
        max_direct_w, max_direct_r

        if large is still too good, consider tweaking
        max_shard, seq_shard

        if metadata refs/updates are too cheap, consider tweaking
        flush_max
"""

from SimFS import FS


# THIS IS ACTUALLY JUST A FORMAT SAMPLE.  THE DATA HAS NOT BEEN CALIBRATED
class zfs(FS):
    """ ZFS simulation """

    def __init__(self, disk, age=0):
        """ Instantiate a XFS simulation. """

        FS.__init__(self, disk, md_span=0.5)
        self.desc = "ZFS"
        if age > 0:
            self.desc += "(%3.1f)" % age

        # THESE VALUES ARE BOGUS!  NEED REAL CALIBRATION!
        self.md_size = 4096
        self.md_seek = 0         # average cylinders from data to metadata

        self.max_shard = 4096 * 1024
        self.seq_shard = False

        self.md_read = {4096: 0.08, 4096 * 1024: 1.05}
        self.md_write = {4096: 0.05, 4096 * 1024: 1.30}
        self.seq_read = {4096: 0.012, 4096 * 1024: 0.40}
        self.seq_write = {4096: 0.095, 4096 * 1024: 0.60}
        self.max_dir_r = {4096: 32, 4096 * 1024: 1}
        self.max_dir_w = {4096: 1, 4096 * 1024: 1}

        self.md_open = 1.0       # one directory read (rest in cache)
        self.md_create = 3.0     # parent directory, directory inode, new inode
        self.md_delete = 2.0     # parent directory, deleted inode

        self.flush_max = 16
        self.flush_bytes = 100000000     # flush after this many bytes
        self.flush_time = 500000         # flush after this much time
