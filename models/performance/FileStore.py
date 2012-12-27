#
# This is intended to be able to simulate the overhead that
# the RADOS filestore adds to standard I/O test patterns
#

class FileStore:
    """ Performance Modeling FileStore  Simulation. """

    # vaguely reasonable parameters
    md_bsize = 4096     # unit of metadata read/write
    j_header = 4096     # size of a journal record header
    sync_time = 500000  # flush interval (in micro-seconds)

    # magic tunables
    md_fraction = 0.01  # fraction of the FS for metadata
    # TODO: calibrate this by smalliobench-fs vs fio read
    md_cache_hit =0.05  # fraction of time we can skip MD reads
    # TODO: calibrate this by smalliobench-fs vs fio write (less above)
    md_rewrite = 0.05   # fraction of time we aggregate MD writes

    def __init__(self, data_fs, journal_fs=None, journal_share=1):
        """ create a file store simulation """

        self.data_fs = data_fs
        self.journal_fs = journal_fs
        self.journal_share = journal_share
        self.fs_size = data_fs.disk.size
        self.md_size = self.md_fraction * self.fs_size

    def read(self, bsize, obj_size, depth=1):
        """ average time for reads """

        # metadata lookup
        mdreads = (float(1) - self.md_cache_hit) ** depth
        time = mdreads * self.data_fs.read(self.md_bsize, self.fs_size, seq=False, depth=depth)

        # data read
        time += self.data_fs.read(bsize, obj_size, seq=False, depth=depth)

        return time

    def write(self, bsize, obj_size, depth=1):
        """ average time for object writes """

        # basic file system data write
        time = self.data_fs.write(bsize, obj_size, seq=False, depth=depth)

        # journal write
        jwrite = self.j_header + bsize
        if self.journal_fs == None:
            # journal in the same file system
            time += self.data_fs.write(self.j_header + bsize, self.fs_size, seq=False, depth=depth)
        else:
            # shared dedicated journal device may have limited throughput
            jtime = self.journal_fs.write(jwrite, self.md_size, sync=True)
            if jtime > time:
                time = jtime

        # metadata lookup
        mdreads = (float(1) - self.md_cache_hit) ** depth
        time += mdreads * self.data_fs.read(self.md_bsize, self.fs_size, seq=False, depth=depth)

        # metadata updates are efficiently aggregated
        mdwrites = (float(1) - self.md_rewrite) ** depth
        d = self.sync_time / time
        if depth > d:
            d = depth
        time += mdwrites * self.data_fs.write(self.md_bsize, self.md_size, seq=False, depth=d)

        return time

    def create(self):
        """ new file creation """

        # metadata lookup
        mdreads = (float(1) - self.md_cache_hit)
        time = mdreads * self.data_fs.read(self.md_bsize, self.fs_size, seq=False)

        # metadata updates are efficiently aggregated
        mdwrites = 3 * (float(1) - self.md_rewrite)
        d = self.sync_time / time
        time += mdwrites * self.data_fs.write(self.md_bsize, self.fs_size, seq=False, depth=d)

        return time

    def delete(self):
        """ file deletion """

        # metadata lookup
        mdreads = (float(1) - self.md_cache_hit)
        time = mdreads * self.data_fs.read(self.md_bsize, self.fs_size, seq=False)

        # metadata updates are efficiently aggregated
        mdwrites = 3 * (float(1) - self.md_rewrite)
        d = self.sync_time / time
        time += mdwrites * self.data_fs.write(self.md_bsize, self.fs_size, seq=False, depth=d)
        return time
