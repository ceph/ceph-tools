#
# RAID reliability models
#
#   NOTE:
#       I got the rebuild rates from Jeff Whitehead.  I'm not
#       sure where he got them from .
#

import RelyFuncts

MB = 1000000     # typical unit for recovery speeds


class RAID:
    """ model a mirrored raid set """

    def __init__(self, disk, volumes, recovery, delay=0, scrub=True):
        """ create a RAID reliability simulation
            volumes -- number of total volumes in set
            recovery -- rebuild rate (bytes/second)
            delay -- rebuild delay (hours)
            parity -- number of parity volumes
        """
        self.disk = disk
        self.speed = recovery
        self.volumes = volumes
        self.delay = delay
        self.scrub = scrub
        self.parity = 0

    def rebuild_time(self):
        seconds = self.disk.size / self.speed
        return float(seconds * RelyFuncts.HOUR) / (60 * 60)

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of data loss during a period """

        # probability of an initial disk failure
        p_fail = self.disk.p_failure(period=period)

        # probability of another failure during re-silvering
        recover = float(self.delay) + self.rebuild_time()
        p_fail2 = self.disk.p_failure(period=recover)

        # how many surviving volumes do I depend on
        from_set = 1 if self.parity == 0 else self.volumes - self.parity

        # consider possibility of NRE during re-silvering
        # BOGUS modeling
        #   the probability is trivial to compute, but the data loss
        #   implications of an NRE during recovery seem imponderable
        p_nre = 0 if self.scrub else \
                self.disk.corrupted_bytes(self.disk.size * from_set)

        # probability of losing the remaining redundancy
        survivors = self.parity if self.parity > 0 else self.volumes - 1
        while survivors > 0:
            p_fail *= ((p_fail2 + p_nre) * from_set)
            survivors -= 1
            from_set -= 1

        return p_fail

    def loss(self):
        """ amount of data lost after a drive failure """
        # which should somehow factor in data lost due to NREs
        return self.disk.size


class RAID1(RAID):
    """ model a mirrored RAID set """

    def __init__(self, disk, volumes=2, recovery=10 * MB, delay=0, scrub=True):
        RAID.__init__(self, disk, volumes=volumes, recovery=recovery, \
                      delay=delay, scrub=scrub)
        self.parity = 0
        self.description = "RAID-1: %d cp" % (volumes)


class RAID5(RAID):
    """ model a RAID set with one parity volume """

    def __init__(self, disk, volumes=3, recovery=5 * MB, delay=0, scrub=True):
        RAID.__init__(self, disk, volumes=volumes, recovery=recovery, \
                      delay=delay, scrub=scrub)
        self.parity = 1
        self.description = "RAID-5: %d+%d" % (volumes - 1, 1)


class RAID6(RAID):
    """ model a RAID set with two parity volumes """

    def __init__(self, disk, volumes=6, recovery=5 * MB, delay=0, scrub=True):
        RAID.__init__(self, disk, volumes=volumes, recovery=recovery, \
                      delay=delay, scrub=scrub)
        self.parity = 2
        self.description = "RAID-6: %d+%d" % (volumes - 2, 2)
