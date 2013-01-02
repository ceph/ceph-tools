#
# RADOS reliability models
#

import RelyFuncts

MB = 1000000     # unit for recovery speed


class RADOS:
    """ model a single-volume RADOS OSD """

    def __init__(self, disk, pg=200, copies=1, speed=50 * MB, delay=0):
        """ create a RADOS reliability simulation
            pg -- number of placement groups per OSD
            copies -- number of copies for these objects
            speed -- expected recovery rate (bytes/second)
            delay -- automatic mark-out interval (hours)
        """
        self.disk = disk
        self.speed = speed
        self.pgs = pg
        self.copies = copies
        self.delay = delay
        self.description = "RADOS: %d cp, %d pg" % (copies, pg)

    def rebuild_time(self):
        seconds = self.disk.size / (self.speed * self.pgs)
        return float(seconds * RelyFuncts.HOUR) / (60 * 60)

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of data loss during a period """

        # probability of an initial disk failure
        p_fail = self.disk.p_failure(period=period)

        # probability of another volume failure during recovery
        recover = float(self.delay) + self.rebuild_time()
        p_fail2 = self.disk.p_failure(period=recover)

        # note that declustering increases the number of volumes
        # upon which we depend
        copies = self.copies - 1
        while copies > 0:
            p_fail *= (p_fail2 * self.pgs)
            copies -= 1

        return p_fail

    def loss(self):
        """ amount of data lost after a drive failure """

        # with perfect declustering (which requires more OSDs
        # than placement groups/osd) we should expect to lose
        # about 1/2 of a placement group as a result of a second
        # drive failure.
        l = self.disk.size
        if self.copies > 1:
            l /= (2 * self.pgs)
        return l
