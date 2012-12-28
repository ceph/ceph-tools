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

    def __init__(self, disk, volumes, recovery):
        """ create a RAID reliability simulation """
        self.disk = disk
        self.speed = recovery
        self.volumes = volumes
        self.parity = 0

    def p_failure(self, period=RelyFuncts.YEAR, scrub=True):
        """ probability of data loss during a period """

        # probability of an initial disk failure
        p_fail = self.disk.p_failure(period=period)

        # probability of another failure during re-silvering
        s_recover = self.disk.size / self.speed
        if self.parity > 0:
            s_recover *= self.volumes - self.parity
        h_recover = float(s_recover) / (60 * 60)
        p_fail2 = self.disk.p_failure(period=h_recover)

        # consider possibility of NRE during re-silvering
        # (BOGUS modeling, best not used)
        p_nre = 0 if scrub else self.disk.corrupted_bytes(self.disk.size)

        # probability of losing all copies
        survivors = self.parity if self.parity > 0 else self.volumes - 1
        while survivors > 0:
            p_fail *= (p_fail2 + p_nre)
            survivors -= 1

        return p_fail

    def loss(self):
        """ amount of data lost after a drive failure """
        return self.disk.size

class RAID1(RAID):
    """ model a mirrored RAID set """

    def __init__(self, disk, volumes=2, recovery=10 * MB):
        RAID.__init__(self, disk, volumes=volumes, recovery=recovery)
        self.parity = 0
        self.description = "RAID-1: %d cp" % (volumes)

class RAID5(RAID):
    """ model a RAID set with one parity volume """

    def __init__(self, disk, volumes=3, recovery=5 * MB):
        RAID.__init__(self, disk, volumes=volumes, recovery=recovery)
        self.parity = 1
        self.description = "RAID-5: %d+%d" % (volumes - 1, 1)


class RAID6(RAID):
    """ model a RAID set with two parity volumes """

    def __init__(self, disk, volumes=6, recovery=5 * MB):
        RAID.__init__(self, disk, volumes=volumes, recovery=recovery)
        self.parity = 2
        self.description = "RAID-6: %d+%d" % (volumes - 2, 2)
