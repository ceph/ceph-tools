#
# RADOS reliability models
#


import RelyFuncts

MARKOUT = 10 * RelyFuncts.MINUTE
RECOVER = 50 * 1000000
FULL = 0.75


class RADOS:
    """ model a single-volume RADOS OSD """

    def __init__(self, disk,
                pg=200,             # recommended
                copies=2,           # recommended minimum
                speed=RECOVER,      # typical large object speed
                delay=MARKOUT,      # default mark-out
                fullness=FULL,      # how full are the volumes
                nre="ignore"):      # scrub largely eliminates these
        """ create a RADOS reliability simulation
            pg -- number of placement groups per OSD
            copies -- number of copies for these objects
            speed -- expected recovery rate (bytes/second)
            delay -- automatic mark-out interval (hours)
            nre -- how to handle NREs (ignore, error, fail)
        """
        self.disk = disk
        self.speed = speed
        self.pgs = pg
        self.copies = copies
        self.delay = delay
        self.full = fullness
        self.nre = nre
        self.description = "RADOS: %d cp" % (copies)

    def rebuild_time(self):
        """ expected time to recover from a drive failure """
        seconds = (self.disk.size * self.full) / (self.speed * self.pgs)
        return seconds * RelyFuncts.SECOND

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of data loss during a period """

        # probability of an initial disk failure
        p_fail = self.disk.p_failure(period=period)

        # probability of another volume failure during recovery
        recover = float(self.delay) + self.rebuild_time()
        p_fail2 = self.disk.p_failure(period=recover, drives=self.pgs)

        # note that declustering increases the number of volumes
        # upon which we depend
        copies = self.copies - 1
        while copies > 0:
            p_fail *= p_fail2
            copies -= 1

        return p_fail

    def p_nre(self):
        """ probability of an NRE during recovery """
        if self.nre == "ignore":
            return 0

        # FIX ... this only works for disk size * nre << 1
        return self.disk.size * self.full * self.disk.nre

    def loss(self):
        """ amount of data lost after a drive failure during recovery """
        # with perfect declustering (which requires more OSDs
        # than placement groups/osd) we should expect to lose
        # about 1/2 of a placement group as a result of a second
        # drive failure.
        l = self.disk.size * self.full
        if self.copies > 1:
            l /= (2 * self.pgs)

        return l

    def loss_nre(self, objsize=0):
        """ amount of data lost by NRE during recovery """
        if self.nre == "ignore":
            return 0

        badBytes = self.disk.corrupted_bytes(self.disk.size)
        pgSize = self.disk.size * self.full / self.pgs
        loss = objsize if objsize > 0 and objsize < pgSize else pgSize

        if self.nre == "fail":
            return loss         # one NRE = one lost object
        elif self.nre == "error":
            return badBytes     # one NRE = one lost byte
        else:   # half lost objects, half undetected errors
            return (badBytes + loss) / 2
