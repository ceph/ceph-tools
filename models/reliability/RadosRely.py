#
# RADOS reliability models
#
#   the modeled unit is a Placement Group
#

import RelyFuncts

MARKOUT = 10 * RelyFuncts.MINUTE
RECOVER = 50 * 1000000
FULL = 0.75

KB = 1024
MB = KB * 1024
GB = MB * 1024


class RADOS:
    """ model a single-volume RADOS OSD """

    def __init__(self, disk,
                pg=200,             # recommended
                copies=2,           # recommended minimum
                speed=RECOVER,      # typical large object speed
                delay=MARKOUT,      # default mark-out
                fullness=FULL,      # how full are the volumes
                objsize=1 * GB,     # average object size
                stripe=4 * MB,      # typical stripe width
                nre="ignore"):      # scrub largely eliminates these
        """ create a RADOS reliability simulation
            pg -- number of placement groups per OSD
            copies -- number of copies for these objects
            speed -- expected recovery rate (bytes/second)
            delay -- automatic mark-out interval (hours)
            objsize -- typical object size
            stripe -- typical stripe width
            nre -- how to handle NREs (ignore, error, fail)
        """
        self.disk = disk
        self.speed = speed
        self.pgs = pg
        self.copies = copies
        self.delay = delay
        self.full = fullness
        self.objsize = objsize
        self.stripe = stripe
        self.nre = nre
        self.size = disk.size * copies  # size of a set of copies
        self.description = "RADOS: %d cp" % (copies)

    def rebuild_time(self):
        """ expected time to recover from a drive failure """
        seconds = (self.disk.size * self.full) / (self.speed * self.pgs)
        return seconds * RelyFuncts.SECOND

    def obj_stripe(self):
        """ the number of OSDs across which a user object is striped """

        if self.stripe == 0 or self.stripe >= self.objsize:
            return 1
        x = self.objsize / self.stripe
        return x if x < self.pgs else self.pgs

    def loss_fraction(self, sites=1):
        """ the fraction of objects that are lost when a drive fails """

        if self.copies <= 1 and sites <= 1:
            return 1
        return float(1) / (2 * self.pgs)

    def durability(self, period=RelyFuncts.YEAR, mult=1):
        """ probability of an arbitrary object surviving the period """

        # probability of losing a all copies of Placement Group
        mult *= self.obj_stripe()
        f = self.p_failure(period=period, mult=mult)

        # but most of the PGs on a failed drive wll survive
        f *= self.loss_fraction()

        return float(1) - f

    def p_failure(self, period=RelyFuncts.YEAR, mult=1):
        """ probability of losing a PG as a result of drive failures
                period -- time over which Pfail should be estimated
                mult -- FIT rate multiplier
        """

        # probability of an initial failure (of any copy)
        p_fail = self.disk.p_failure(period=period, mult=mult * self.copies)

        # probability of losing backups before we can recover
        recover = float(self.delay) + self.rebuild_time()
        if self.copies > 1:
            # probability of losing the second copy of this PG
            p_fail *= self.disk.p_failure(period=recover, mult=self.pgs)

            # probability of losing any additional copies
            copies = self.copies - 2
            while copies > 0:
                p_fail *= self.disk.p_failure(period=recover, mult=copies)
                copies -= 1

        return p_fail

    def p_nre(self):
        """ probability of an NRE during recovery """
        if self.nre == "ignore":
            return 0

        # FIX ... this only works for disk size * nre << 1
        return self.disk.size * self.full * self.disk.nre

    def loss(self, period=RelyFuncts.YEAR, per=0):
        """ amouint of data lost as a result of drive failures
            period -- over which we are calculating loss
            per -- 0 -> drive, else size of the farm
        """

        # we could, in principle lose a whole drive worth of data
        l = self.disk.size * self.full * self.loss_fraction()

        # scale this up to the specified farm size
        if per > 0:
            l *= per / (self.copies * self.disk.size)

        return l

    def loss_nre(self):
        """ amount of data lost by NRE during recovery """
        if self.nre == "ignore":
            return 0

        badBytes = self.disk.corrupted_bytes(self.disk.size)
        pgSize = self.disk.size * self.full / self.pgs
        loss = self.objsize if self.objsize > 0 and self.objsize < pgSize \
                else pgSize

        if self.nre == "fail":
            return loss         # one NRE = one lost object
        elif self.nre == "error":
            return badBytes     # one NRE = one lost byte
        else:   # half lost objects, half undetected errors
            return (badBytes + loss) / 2
