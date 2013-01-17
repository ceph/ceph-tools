#
# This is intended to be able to simulate the overhead that
# the RADOS filestore adds to standard I/O test patterns
#
# TODO: mark says nobody gets better than 80MB/s write through filestore
#       make sure I can model why
# TODO: make sure I can duplicate the ALU filestore data

import math


class FileStore:
    """ Performance Modeling FileStore  Simulation. """

    # vaguely reasonable parameters
    md_bsize = 4096        # unit of metadata read/write
    j_header = 4096        # size of a journal record header
    block_sz = 512 * 1024  # unit of I/O aggregation
    sync_time = 50000000   # flush interval (in micro-seconds)
    md_cache_sz = 2000     # number of objects we cache

    # magic tunables
    md_fraction = .001  # fraction of disk containing metadata

    def __init__(self, data_fs, journal_fs=None, journal_share=1, nobj=2500):
        """ create a file store simulation """

        self.data_fs = data_fs
        self.journal_fs = journal_fs
        self.journal_share = journal_share
        self.nobj = nobj

        # bad approximations
        self.md_seek = self.md_fraction * data_fs.disk.size
        self.seek = data_fs.disk.size       # pessimistic
        self.hit_rate = 1 if nobj <= self.md_cache_sz \
                        else float(self.md_cache_sz) / nobj

    def md_reads(self, bsize, obj_size):
        """ number of metadata reads to find desired data """
        return 1

    def md_writes(self, bsize, obj_size):
        """ number of metadata updates to write to an object """
        return 1

    def read(self, bsize, obj_size, depth=1):
        """ average time for reads """

        # some metadata reads are saved by the cache
        mdr = self.md_reads(bsize, obj_size)
        mdr *= 1.0 - self.hit_rate
        time = mdr * self.data_fs.read(self.md_bsize, self.seek,
            seq=False, depth=depth)

        # plus time for the (random) data read
        time += self.data_fs.read(bsize, self.seek,
            seq=False, depth=depth)

        return time

    def write(self, bsize, obj_size, depth=1):
        """ average time for object writes """

        # some metadata reads are saved by the cache
        mdr = self. md_reads(bsize, obj_size)
        mdr *= 1.0 - self.hit_rate
        time = mdr * self.data_fs.read(self.md_bsize, self.seek,
            seq=False, depth=depth)
        mdw = self.md_writes(bsize, obj_size)

        # journal in the same file sysetm as the data
        if self.journal_fs == None:
            jt = self.data_fs.write(self.j_header + bsize, self.seek,
                                seq=True, sync=True, depth=depth)
            dt = self.data_fs.write(bsize, self.seek,
                                seq=False, sync=True, depth=depth)
            mt = mdw * self.data_fs.write(self.md_bsize, self.seek,
                                seq=False, sync=True, depth=depth)
            return time + jt + dt + mt
        else:   # separate journal
            jt = self.journal_fs.write(self.j_header + bsize, self.seek,
                                seq=False, sync=True, depth=depth)
            jt *= self.journal_share        # FIX this seems wrong
            dt = self.data_fs.write(bsize, obj_size,
                                seq=False, depth=depth)
            mt = mdw * self.data_fs.write(self.md_bsize, self.md_seek,
                                seq=False, depth=depth)

            # compute expected data and metadata write aggregation
            sameobj = float(self.sync_time) / ((dt + mt) * self.nobj)
            Pso = 1.0 - math.exp(-sameobj)
            mt /= 1 + Pso
            sameblk = float(self.block_sz) / obj_size
            Psb = 1.0 - math.exp(-1 * sameobj * sameblk)
            dt /= 1 + Psb

            # in principle, journal and data writes are parallel
            if depth < 2:
                return jt + dt + mt
            elif jt > dt + mt:
                return time + jt
            else:
                return time + dt + mt

    def create(self):
        """ new file creation """
        return 666

    def delete(self):
        """ file deletion """
        return 666
