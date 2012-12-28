#
# RAID reliability models
#

import RelyFuncts

MBS = 100000     # megabytes per second

class RAID1:
    """ model a mirrored raid set """

    def __init__(self, disk, volumes=2, speed=100 * MBS):
        """ create a RAID reliability simulation """
        self.disk = disk
        self.speed = speed
        self.volumes = volumes
        self.parity = 0

    def p_failure(self, period=RelyFuncts.YEAR, scrub=False):
        """ probability of data loss during a period """

        # probability of an initial disk failure
        p_fail = self.disk.p_failure(period=period)

        # probability of another failure during re-silvering
        s_recover = self.disk.size / self.speed
        if self.parity > 0:
            s_recover *= self.volumes - self.parity
        h_recover = float(s_recover) / (60 * 60)
        p_fail2 = self.disk.p_failure(period=h_recover)

        # also consider possibility of NRE during re-silvering
        p_nre = 0 if scrub else self.disk.corrupted_bytes(self.disk.size)

        # probability of losing all copies
        copies = self.parity if self.parity > 0 else self.volumes - 1
        while copies > 0:
            p_fail *= (p_fail2 + p_nre)
            copies -= 1

        return p_fail


class RAID5(RAID1):
    """ model a RAID set with one parity volume """

    def __init__(self, disk, volumes=6, speed=100 * MBS):
        RAID1.__init__(self, disk, volumes=volumes, speed=speed)
        self.parity = 1


class RAID6(RAID1):
    """ model a RAID set with two parity volumes """

    def __init__(self, disk, volumes=6, speed=100 * MBS):
        RAID1.__init__(self, disk, volumes=volumes, speed=speed)
        self.parity = 2
