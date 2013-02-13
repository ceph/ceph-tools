#
# basic disk reliability model
#
#   the modeled unit is one drive
#

import RelyFuncts

M = 1000000
G = M * 1000
T = G * 1000
P = T * 1000


class Disk:

    def __init__(self, size, fits, nre, desc):
        """ create a disk reliability simulation
            size -- in bytes
            fits -- failures per billion hours
            nre -- non-recoverable errors per byte
            desc -- description for reporting purposes
        """
        self.size = size
        self.fits = fits
        self.nre = nre
        self.description = desc

    def durability(self, period=RelyFuncts.YEAR, mult=1):
        """ probability of an arbitrary object surviving the period
            period -- over which we want to model reliability
            mult -- FIT rate multiplier
        """

        return RelyFuncts.Pn(self.fits * mult, period, n=0)

    def p_failure(self, period=RelyFuncts.YEAR, mult=1):
        """ probability of drive failure during a period
            period -- over which we want to model reliability
            mult -- FIT rate multiplier
        """
        return float(1) - RelyFuncts.Pn(self.fits * mult, period, n=0)

    def loss(self, period=RelyFuncts.YEAR, per=0):
        """ amouint of data lost after a drive failure
            period -- over which we are calculating loss
            per -- 0 -> drive, else size of the farm
        """
        return self.size if per == 0 else per

    def p_nre(self):
        """ probability of NRE during recovery """
        return 0        # meaningless for a single disk

    def loss_nre(self, period=RelyFuncts.YEAR):
        """ expected data loss due to NRE's during recovery """
        return 0        # meaningless for a single disk

    def corrupted_bytes(self, bytecount):
        """ number of bytes expected to be lost due to NRE """
        return float(self.nre) * bytecount


class EnterpriseDisk(Disk):
    """ Spec'd Enterprise Drive (Seagate Barracuda) """

    def __init__(self, size=2 * T):
        Disk.__init__(self, size=size, fits=826, nre=1.0e-15,
                    desc="Enterprise drive")


class ConsumerDisk(Disk):
    """ Spec'd Consumer Drive (Seagate Barracuda) """

    def __init__(self, size=2 * T):
        Disk.__init__(self, size=size, fits=1320, nre=1.0e-14,
                    desc="Consumer drive")


class RealDisk(Disk):
    """ Specs from Schroeders 2007 FAST paper """

    def __init__(self, size=2 * T):
        Disk.__init__(self, size=size, fits=7800, nre=1.0e-14,
                    desc="real-world disk")
