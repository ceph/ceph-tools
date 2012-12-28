#
# RAID reliability models
#

import RelyFuncts

MBS = 100000     # megabytes per second

class RADOS:
    """ model a RADOS pool """

    def __init__(self, disk, pools=200, copies=1, speed=100 * MBS):
        """ create a RAID reliability simulation """
        self.disk = disk
        self.speed = speed
        self.pools = pools
        self.copies = copies

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of data loss during a period """

        # probability of an initial disk failure
        p_fail = self.disk.p_failure(period=period)

        # probability of another failure during re-silvering
        s_recover = self.disk.size / (self.speed * self.pools)
        h_recover = float(s_recover) / (60 * 60)
        p_fail2 = self.disk.p_failure(period=h_recover)

        # probability of losing all remaining copies
        copies = self.copies - 1
        while copies > 0:
            p_fail *= p_fail2
            copies -= 1

        return p_fail
