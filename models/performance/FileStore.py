#
# This is intended to be able to simulate the overhead that
# the RADOS filestore adds to standard I/O test patterns
#

import Poisson


class FileStore:
    """ Performance Modeling FileStore  Simulation. """

    # vaguely reasonable parameters
    md_bsize = 4096        # unit of metadata read/write
    j_header = 4096        # size of a journal record header
    block_sz = 512 * 1024  # unit of write aggregation
    sync_time = 5000000    # flush interval (in micro-seconds)

    # magic tunables
    md_fraction = .001     # fraction of disk containing metadata
    md_cache_sz = 2000     # number of objects we cache

    def __init__(self, data_fs, journal_fs=None, journal_share=1):
        """ create a file store simulation
            data_fs -- SimFS for the data file system
            journal_fs -- SimFS for the journal (none if useing data disk)
            journal_share -- how many OSDs share the journal device
        """
        self.data_fs = data_fs
        self.journal_fs = journal_fs
        self.journal_share = journal_share

        # bad approximations of typical seek distances
        self.md_seek = self.md_fraction * data_fs.disk.size
        self.seek = data_fs.disk.size

    def miss_rate(self, nobj):
        """ expected meta-data lookup cache miss rate """
        r = float(nobj) / self.md_cache_sz
        return 1 - r if r < 1 else 0

    def md_reads(self, bsize, obj_size):
        """ number of metadata reads to find desired data """
        return 1

    def md_writes(self, bsize, obj_size):
        """ number of metadata updates to write to an object """
        return 1

    def read(self, bsize, obj_size, depth=1, nobj=2500):
        """ average time for reads """

        # figure out how much metadata we will actually read
        mdr = self.md_reads(bsize, obj_size) * self.miss_rate(nobj)

        # figure out how long it will take to do the I/O
        mt = self.data_fs.read(self.md_bsize, self.seek,
                    seq=False, depth=depth)
        dt = self.data_fs.read(bsize, self.seek, seq=False, depth=depth)
        return dt + (mdr * mt)

    def write(self, bsize, obj_size, depth=1, nobj=2500):
        """ average time for object writes """

        # figure out how much metadata we will actually read
        mdr = self.md_reads(bsize, obj_size) * self.miss_rate(nobj)
        lt = mdr * self.data_fs.read(self.md_bsize, self.seek,
                                seq=False, depth=depth)

        mdw = self.md_writes(bsize, obj_size)
        if self.journal_fs == None:     # journal on the data device
            jt = self.data_fs.write(self.j_header + bsize, self.seek,
                                seq=True, sync=True, depth=depth)
            dt = self.data_fs.write(bsize, self.seek,
                                seq=False, sync=True, depth=depth)
            mt = mdw * self.data_fs.write(self.md_bsize, self.seek,
                                seq=False, sync=True, depth=depth)
            return lt + jt + dt + mt
        else:   # separate journal
            jt = self.journal_fs.write(self.j_header + bsize, self.seek,
                                seq=False, sync=True, depth=depth)
            jt *= self.journal_share        # FIX this seems wrong
            dt = self.data_fs.write(bsize, obj_size,
                                seq=False, depth=depth)
            mt = mdw * self.data_fs.write(self.md_bsize, self.md_seek,
                                seq=False, depth=depth)

            # compute expected metadata write aggregation
            ops_per_sync = self.sync_time / (dt + mt)
            PsO = Poisson.PnPlus(float(1) / nobj, ops_per_sync, 2)
            mt /= 1 + PsO

            # compute expected data aggregation (precious little)
            tot_blocks = nobj * obj_size / self.block_sz
            PsB = Poisson.PnPlus(float(1) / tot_blocks, ops_per_sync, 2)
            dt /= 1 + PsB

            # in principle, journal and data writes are parallel
            if depth < 2:
                return lt + jt + dt + mt
            elif jt > dt + mt:
                return lt + jt
            else:
                return lt + dt + mt

    def create(self):
        """ new file creation """

        # FIX: I just made this up
        HUGE = 1000000000000            # big enough to avoid cache hits
        return self.data_fs.create() + self.write(self.md_bsize, HUGE)

    def delete(self):
        """ file deletion """

        # FIX: I just made this up
        return self.data_fs.delete() + self.write(0, self.block_sz)
