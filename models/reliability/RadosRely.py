#
# RADOS reliability models
#

import RelyFuncts

MB = 1000000     # unit for recovery speed

class RADOS:
    """ model a RADOS pool """

    def __init__(self, disk, pg=200, copies=1, speed=50 * MB, delay=0):
        """ create a RAID reliability simulation
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

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of data loss during a period """
   
        # probability of an initial disk failure
        p_fail = self.disk.p_failure(period=period)

        # probability of further failures during re-silvering
        #   
        #   Note that parallel recovery is (to a first approximation)
        #   a reliability wash, as the reduced recovery time is (almost
        #   exactly) compensated for by the increased number of volumes
        #   whose failures can impact the recovery
        s_recover = self.disk.size / self.speed
        h_recover = float(self.delay) + (s_recover / (60 * 60))
        p_fail2 = self.disk.p_failure(period=h_recover)
        
        copies = self.copies - 1
        while copies > 0:
            p_fail *= p_fail2
            copies -= 1

        return p_fail

    def loss(self):
        """ amount of data lost after a drive failure """

        # NOTE: this assumes perfect declustering, which is
        #   untrue if the number of placement groups per OSD
        #   is greater than the number of OSDs
        return self.disk.size / self.pgs

