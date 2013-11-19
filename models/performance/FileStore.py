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
This is intended to be able to simulate the overhead that
the RADOS filestore adds to standard I/O test patterns

NOTE:
   we are modeling the time to perform a single operation,
   but these are fundamentally throughput models, so it should
   be assumed that another operation will come immediately
   after the one we are simulating.
"""

import Poisson
from units import *


class FileStore:
    """ Performance Modeling FileStore  Simulation. """

    # vaguely reasonable parameters
    md_bsize = 4096        # unit of metadata read/write
    j_header = 4096        # size of a journal record header
    block_sz = 512 * 1024  # unit of write aggregation
    sync_time = 5000000    # flush interval (in micro-seconds)

    # magic tunables (to which we shouldn't be all that sensitive)
    md_fraction = .001     # fraction of FS containing metadata
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
        self.md_seek = self.md_fraction * data_fs.size
        self.seek = data_fs.size

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
        (mt, bw, us) = self.data_fs.read(self.md_bsize, self.seek,
                                         seq=False, depth=depth)
        (dt, bw, us) = self.data_fs.read(bsize, self.seek,
                                         seq=False, depth=depth)
        #print("FS-r: raw mdr=%f, mt=%d, dt=%d" % (mdr, mt, dt))
        dt *= self.d_miss_rate(nobj, obj_size)
        #print("FS-r: adj dt=%d" % (dt))
        # FIX ... read - use b/w returned by the data/metadata reads
        # FIX ... read - pass through the disk and CPU utilization info
        # FIX ... read - compute the cpu utilization in the OSDs
        return dt + (mdr * mt)

    def write(self, bsize, obj_size, depth=1, nobj=2500):
        """ average time for object writes """

        # figure out how much metadata we will actually read
        mdr = self.md_reads(bsize, obj_size) * self.md_miss_rate(nobj)
        (lt, bw, us) = self.data_fs.read(self.md_bsize, self.seek,
                                         seq=False, depth=depth)
        lt *= mdr

        mdw = self.md_writes(bsize, obj_size)
        if self.journal_fs is None:     # journal on the data device
            (jt, bw, us) = self.data_fs.write(self.j_header + bsize, self.seek,
                                              seq=True, sync=True,
                                              depth=depth)
            (dt, bw, us) = self.data_fs.write(bsize, self.seek,
                                              seq=False, sync=True,
                                              depth=depth)
            dt *= self.d_miss_rate(nobj, obj_size)
            (mt, bw, us) = self.data_fs.write(self.md_bsize, self.seek,
                                              seq=False, sync=True,
                                              depth=depth)
            mt *= mdw
            # FIX ... write - use b/w returned by the data/metadata writes
            # FIX ... write - pass through the disk and CPU utilization info
            # FIX ... write - compute the cpu utilization in the OSDs
            return lt + jt + dt + mt
        else:   # separate journal
            (jt, bw, us) = self.journal_fs.write(self.j_header + bsize,
                                                 self.seek, seq=False,
                                                 sync=True, depth=depth)
            jt *= self.journal_share        # FIX this seems wrong
            (dt, bw, us) = self.data_fs.write(bsize, obj_size,
                                              seq=False, depth=depth)
            (mt, bw, us) = self.data_fs.write(self.md_bsize,
                                              self.md_seek,
                                              seq=False, depth=depth)
            mt *= mdw
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

            # FIX ... write - use b/w returned by the data/metadata writes
            # FIX ... write - pass through the disk and CPU utilization info
            # FIX ... write - compute the cpu utilization in the OSDs

            # in principle, journal and data writes are parallel
            if jt > dt + mt:
                if not "journal caps" in self.warnings:
                    msg = "\n\tjournal caps throughput "
                    msg += "for %d parallel %d byte writes"
                    self.warnings += msg % (self.journal_share, bsize)
                return lt + jt
            else:
                return lt + dt + mt

    def create(self):
        """ new file creation """

        # FIX: really implement filestore creates
        HUGE = 1000000000000            # big enough to avoid cache hits
        return self.data_fs.create() + self.write(self.md_bsize, HUGE)

    def delete(self):
        """ file deletion """

        # FIX: really implement filestore deletes
        return self.data_fs.delete() + self.write(0, self.block_sz)


# helper function to create filestore simulations
def makefilestore(datafs, journalfs, dict):
    """ instantiate a filestore simulation from a dict
        datafs -- fs for data
        journalfs -- fs for journal
        dict -- other parameters
            osd_per_journal: number of OSD sharing each journal
    """

    if journalfs is not None and 'osd_per_journal' in dict:
        share = dict['osd_per_journal']
    else:
        share = 1
    fstore = FileStore(datafs, journalfs, share)
    return fstore


from Report import Report


def filestoretest(fs, dict, descr=""):
    """
    exercise a file system with tests described in a dict
        fs -- device to be tested
        dict --
            SioFsize ... size of test file
            SioFdepth ... list of request depths
            SioFbs ... list of block sizes
            SioFnobj ... number of objects to spread requests over
            Smisc ... include creates and deletes
    """

    dflt = {        # default throughput test parameters
        'SioFsize': 16 * MEG,
        'SioFdepth': [1, 32],
        'SioFbs': [4096, 128 * 1024, 4096 * 1024],
        'SioFnobj': 2500,
        'Smisc': False,
    }

    sz = dict['SioFsize'] if 'SioFsize' in dict else dflt['SioFsize']
    depths = dict['SioFdepth'] if 'SioFdepth' in dict else dflt['SioFdepth']
    bsizes = dict['SioFbs'] if 'SioFbs' in dict else dflt['SioFbs']
    no = dict['SioFnobj'] if 'SioFnobj' in dict else dflt['SioFnobj']
    misc = dict['Smisc'] if 'Smisc' in dict else dflt['Smisc']

    # are we doing create delete as well
    if misc:
        print("Basic operations to %s" % (descr))
        r = Report(("create", "delete"))
        (tc, bwc, loadc) = fs.create()
        (td, bwd, loadd) = fs.delete()

        r.printHeading()
        r.printIOPS(1, (bwc, bwd))
        r.printLatency(1, (tc, td))
        print("")

    for d in depths:
        print("smalliobench-fs, %s, depth=%d" % (descr, d))
        print("\tnobj=%d, objsize=%d" % (no, sz))
        r = Report(("rnd read", "rnd write"))
        r.printHeading()
        for bs in bsizes:
            # NOTE: it is no longer obvious to me why I am overriding depth
            #       surely I had a reason for it when I wrote this code :-(
            trr = fs.read(bs, sz, depth=1, nobj=no)
            irr = SECOND / trr
            brr = irr * bs
            trw = fs.write(bs, sz, depth=d, nobj=no)
            irw = SECOND / trw
            brw = irw * bs

            r.printBW(bs, (brr, brw))
            r.printIOPS(0, (irr, irw))
        #   r.printLatency(0, (trr, trw))
        print("")


#
# instantiate a filestore and run a set of basic tests
#
if __name__ == '__main__':

        from SimDisk import makedisk
        disk = makedisk({'device': 'disk'})
        from SimFS import makefs
        fs = makefs(disk, {})

        fs1 = makefilestore(fs, None, {})
        fs2 = makefilestore(fs, fs, {})

        for f in (fs1, fs2):
            msg = "data FS (%s on %s), journal " % \
                (f.data_fs.desc, f.data_fs.disk.desc)
            if f.journal_fs is None:
                msg += "on data disk"
            else:
                msg += "(%s on %s)" % \
                    (f.journal_fs.desc, f.journal_fs.disk.desc)
            filestoretest(f, {}, descr=msg)
