#
# This is intended to be able to simulate disk drives with a range of
# smarts.  It is probably pretty accurate with respect to random access
# performance (which is dominated by physics) but only a crude approximation
# for small-block sequential access (which is dominated by  caching.
# Fortunately, small-block streaming is not (for us) a typical load.
#

import math

# we measure time in microseconds
SECOND = 1000000

# disk capacity and bandwidth are in powers of TEN
MEGABYTE = 1000 * 1000
GIGABYTE = 1000 * 1000 * 1000
TERABYTE = 1000 * 1000 * 1000 * 1000


class Disk:
    """ Performance Modeling Disk Simulation. """

    # fundamental drive characterizing parameters
    #   default values represent enterprise state-of-the-art
    settle_read = 800               # us: optimistic read settle-down
    write_delta = 600               # us: penalty for full settle-down
    max_seek = 13000                # us: full stroke seek time
    avg_seek = 5500                 # us: full stroke/3
    max_depth = 128                 # max concurrent queued operations
    do_writeback = True             # drive does write-back (vs writethrough)
    do_readahead = True    	    # drive does read-ahead caching
    sched_rotate = True             # latency optimization scheduling

    # pseudo-magic numbers to approximate complex behavior
    cache_multiplier = 96            # ideal read-ahead
    cache_max_tracks = 4             # max amount to cache
    cache_max_depth = 5              # max depth multiplier

    def __init__(self, rpm=7200, size=2 * TERABYTE,
                bw=150 * MEGABYTE, heads=10):
        """ Instantiate a disk simulation. """
        self.rpm = rpm
        self.size = size
        self.media_speed = bw
        self.heads = heads

        # infer track/cylinder size from rpm and media speed
        self.trk_size = bw / (rpm / 60)
        self.cyl_size = self.trk_size * heads
        self.cylinders = size / self.cyl_size

    def cylinders_in(self, bytes):
            """ determine how many cylinders a byte range spans """
            return 1 + (bytes / self.cyl_size)

    # Real seek time is quite complex, involving acceleration,
    # deceleration, and settle-down.  I approximate this by
    # choosing the lesser of two functions:
    #
    #   Long seeks are easy to do well because they are
    #   an afine-linear function of the distance.  Compute the
    #   crusing speed based on the difference between the average
    #   and max seek times, and then extrapolate that back
    #   (from the maximum seek time).
    #
    #   Short seeks are much harder.  But we do know that a single
    #   cylinder seek takes about the same amount of time as a
    #   read settle-down.  I arbitrarily attribute half of the
    #   read settle-down time to head motion, and multiply that
    #   by the number of cylinders
    #
    def seekTime(self, cyls, read=True):
        """ Time (us) to perform a seek across # cylinders. """

        if cyls < 1:
            return 0
        elif cyls >= self.cylinders:
            travel = self.max_seek
        else:
            # compute equilibrium long seek rate and extrapolate back
            delta_us = self.max_seek - self.avg_seek
            delta_cyl = 2 * self.cylinders / 3
            us_per_cyl = float(delta_us) / delta_cyl    # marginal seek speed
            long_seek = self.max_seek - ((self.cylinders - cyls) * us_per_cyl)

            # crudely estimate short seek rate from the read settle_down time
            short_seek = self.settle_read + ((cyls - 1) * self.settle_read / 2)

            # choose the lesser of these two numbers
            travel = min(short_seek, long_seek)

        return travel if read else travel + self.write_delta

    # Transfer time is also pretty easy.  The main trick here is that
    # I include the cost of operations that spill over into the next
    # cylinder
    def xferTime(self, bytes, read=True):
        """ Time (us) to perform a read or write of # bytes. """

        # to the extent that cache hits are the result of read-ahead, even
        # cached data reads are ultimately limited to media speed
        time = bytes * SECOND / self.media_speed

        # consider possibility this operation will spill into the next cylinder
        #   (track skew makes track overflow a non-issue)
        seeks = float(bytes) / self.cyl_size
        time += seeks * \
            (self.settle_read if read else self.settle_read + self.write_delta)
        return time

    #
    # VOODO ALERT
    #
    # There are thousands of lines of code in a disk controller
    # to implement read-ahead and write-back caching ... which
    # dominate small sequential I/O and small random writes.
    #
    # This is a painfully poor approximation of that stuff, but it
    # kind of matches some observed behavior and is only intended
    # to put a box around the expected performance.
    #
    def cache_size(self, size, read, depth=1):
        """ Estimate a non-aggressive read-ahead cache size """

        # make sure that caching is enabled
        if read and not self.do_readahead:
            return 0
        if not read and not self.do_writeback:
            return 0

        # 1. don't try to get more than a track ahead
        if size > self.trk_size:
            return 0

        # 2. we cache up to a maximum mulltiplier
        c = size * self.cache_multiplier

        # 3. we are willing to go farther if we see more requests
        c *= min(depth, self.cache_max_depth)

        # 4. but only up to a total maximum amount
        m = self.cache_max_tracks * self.trk_size
        return min(c, m)

    # this method tries to simulate the interplay of
    # queue depth, read-ahead, and write back to figure
    # out how often we can avoid rotational latency waits
    def latency(self, size, read=True, seq=True, depth=1):
        """ Time (us) a request is likely to incur awaiting rotation """

        # start out with the average rotational latency
        l = (SECOND / (self.rpm / 60)) / 2 if self.rpm > 0 else 0

        # figure out how many of these operations I can cache
        c = self.cache_size(size, read, depth)
        n = (c / size) if c > size else 1

        # sequential is about caching AND seek/latency optimization
        if seq:
            if n > 1:
                return l / n        # 1 op in N is spills out of the cache
            if depth > 1:
                return l / depth    # latency optimize queued requests

        # random is mostly seek/latency optimization
        elif self.sched_rotate:
            if read:            # best among parallel requests
                l /= depth
            else:
                if depth > n:   # best among parallel requests
                    l /= depth
                elif n > 1:     # best among cached writes
                    l /= n
                elif c > 0:
                    l /= 2      # mere writeback is two requeest queueing
        return l

    # this method ties all the rest together into a simulation
    # of the average time to do a standard throughput test
    # (for random I/O we ignore coincidental same-cylinder hits)
    def avgTime(self, bsize, file_size, read=True, seq=True, depth=1):
        """ average operation time (us) for a specified test. """

        # transfer time includes intra-transfer-seeks
        tXfer = self.xferTime(bsize, read)

        # requests can't queue deeper than the drive supports
        if depth > self.max_depth:
            depth = self.max_depth
        tLatency = self.latency(bsize, read, seq, depth)

        if seq:
            return tXfer + tLatency
        else:
            cyls = self.cylinders_in(file_size)
            avgcyls = cyls / (depth + 2)
            tSeek = self.seekTime(avgcyls, read)
            return tXfer + tLatency + tSeek

    # convenience functions to plug in operation (and optionally seq)
    def avgRead(self, bsize, file_size, seq=False, depth=1):
        """ average time (us) for a specified read test. """
        return self.avgTime(bsize, file_size, read=True, seq=seq, depth=depth)

    def avgWrite(self, bsize, file_size, seq=False, depth=1):
        """ average time (us) for a specified write test. """
        return self.avgTime(bsize, file_size, read=False, seq=seq, depth=depth)


#
# To save people the trouble of figuring out which parameters
# to cripple to create a dumb disk, I supply one
#
class DumbDisk(Disk):

    def __init__(self, rpm=7200, size=2 * TERABYTE,
                bw=150 * MEGABYTE, heads=10):
        """ Instantiate a dumb disk simulation. """

        Disk.__init__(self, rpm, size, bw, heads)

        self.do_writeback = False
        self.do_readahead = False
        self.sched_rotate = False
        self.max_depth = 1
        self.settle_read = 1000
        self.write_delta = 1000
        self.max_seek = 20000
        self.avg_seek = 8000


#
# SSD's are much simpler than disks
#
#   FIX - the max IOPS modeling is way too simplistic
#       it is depth dependent
#         d=1 5000 * 4K/s
#         d=8 32000 * 4K/s
#         d=32 48000 * 4K/s (hit the b/w limit)
class SSD(Disk):
    """ Performance Modeling SSD simulation. """

    def __init__(self, size, bw=200 * MEGABYTE, iops=20000, streams=1):
        self.size = size
        self.media_speed = bw
        self.max_iops = iops		# single stream
        self.max_depth = streams

        # magic numbers to model more complex behavior
        self.write_penalty = 1.05   # allocation overhead

        # tell a consistent story about the device
        self.rpm = 0
        self.settle_read = 0
        self.write_delta = 0    # is there a write cost?
        self.max_seek = 0
        self.avg_seek = 0
        self.heads = 1
        self.cylinders = 1
        self.cyl_size = self.size / self.cylinders
        self.trk_size = self.cyl_size / self.heads

    def avgTime(self, bsize, file_size, read=True, seq=True, depth=1):
        """ average operation time (us) for a specified test. """

        tXfer = self.xferTime(bsize, read)
        if not read:
            tXfer *= self.write_penalty

        # IOPS limitations ... which depend on the number of streams
        setup = SECOND / self.max_iops
        setup /= depth if depth < self.max_depth else self.max_depth

        return setup + tXfer
