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
This is intended to be able to simulate the overhead that
the RADOS filestore adds to standard I/O test patterns

NOTE:
   we are modeling the time to perform a single operation,
   but these are fundamentally throughput models, so it should
   be assumed that another operation will come immediately
   after the one we are simulating.
"""

import Poisson

GIG = 1000000000


class FileStore:
    """ Performance Modeling FileStore  Simulation. """

    # vaguely reasonable parameters
    md_bsize = 4096        # unit of metadata read/write
    j_header = 4096        # size of a journal record header
    block_sz = 512 * 1024  # unit of write aggregation
    sync_time = 5000000    # flush interval (in micro-seconds)

    # magic tunables (to which we shouldn't be all that sensitive)
    md_fraction = .001     # fraction of disk containing metadata
    md_cache_sz = 2500     # number of objects we cache
    rd_cache_sz = 1 * GIG  # available data cache

    CACHE_WARN = 0.05       # too high a hit rate is probably wrong
    warnings = ""           # I didn't want these to come out in mid test

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

    def md_miss_rate(self, nobj):
        """ expected meta-data lookup cache miss rate """
        r = float(self.md_cache_sz) / float(nobj)
        #if r > self.CACHE_WARN and not "to meta-data cache" in self.warnings:
        #  msg = "\n\t%d objects too few relative to meta-data cache" % (nobj)
        #  self.warnings += msg
        return 1 - r if r < 1 else 0

    def d_miss_rate(self, nobj, obj_size):
        """ expected data lookup cache miss rate """
        r = float(self.rd_cache_sz) / (nobj * obj_size * self.journal_share)
        if r > self.CACHE_WARN and not "to data cache" in self.warnings:
            msg = "\n\t%d x %d byte objects too small relative to data cache"
            self.warnings += msg % (nobj, obj_size)
        return 1 - r if r < 1 else 0

    def md_reads(self, bsize, obj_size):
        """ number of metadata reads to find desired data """
        return 1

    def md_writes(self, bsize, obj_size):
        """ number of metadata updates to write to an object """
        return 0.7      # this is a fudge factor

    def read(self, bsize, obj_size, depth=1, nobj=2500):
        """ average time for reads """

        # figure out how much metadata we will actually read
        mdr = self.md_reads(bsize, obj_size) * self.md_miss_rate(nobj)

        # figure out how long it will take to do the I/O
        mt = self.data_fs.read(self.md_bsize, self.seek,
                    seq=False, depth=depth)
        dt = self.data_fs.read(bsize, self.seek, seq=False, depth=depth)
        #print("FS-r: raw mdr=%f, mt=%d, dt=%d" % (mdr, mt, dt))
        dt *= self.d_miss_rate(nobj, obj_size)
        #print("FS-r: adj dt=%d" % (dt))
        return dt + (mdr * mt)

    def write(self, bsize, obj_size, depth=1, nobj=2500):
        """ average time for object writes """

        # figure out how much metadata we will actually read
        mdr = self.md_reads(bsize, obj_size) * self.md_miss_rate(nobj)
        lt = mdr * self.data_fs.read(self.md_bsize, self.seek,
                                seq=False, depth=depth)

        mdw = self.md_writes(bsize, obj_size)
        if self.journal_fs == None:     # journal on the data device
            jt = self.data_fs.write(self.j_header + bsize, self.seek,
                                seq=True, sync=True, depth=depth)
            dt = self.data_fs.write(bsize, self.seek,
                                seq=False, sync=True, depth=depth)
            dt *= self.d_miss_rate(nobj, obj_size)
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
            #print("FS-w: raw lt=%d, jt=%d, dt=%d, mt=%d" % (lt, jt, dt, mt))

            # compute expected metadata write aggregation
            ops_per_sync = self.sync_time / (dt + mt)
            PsO = Poisson.PnPlus(float(1) / nobj, ops_per_sync, 2)
            mt /= 1 + PsO                           # sloppy math

            # compute expected data aggregation and cache hits
            tot_blocks = nobj * obj_size / self.block_sz
            PsB = Poisson.PnPlus(float(1) / tot_blocks, ops_per_sync, 2)
            dt /= 1 + PsB                           # sloppy math
            dt *= self.d_miss_rate(nobj, obj_size)  # sloppy math
            #print("FS-w: adj lt=%d, jt=%d, dt=%d, mt=%d" % (lt, jt, dt, mt))

            # in principle, journal and data writes are parallel
            if jt > dt + mt:
                if not "journal caps" in self.warnings:
                    msg = "\n\tjournal caps throughput for %d parallel %d byte writes"
                    self.warnings += msg % (self.journal_share, bsize)
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
