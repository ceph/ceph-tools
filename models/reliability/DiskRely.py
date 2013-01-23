#
# basic disk reliability model
#

import RelyFuncts

MB = 1000000
GB = MB * 1000
TB = GB * 1000
PB = TB * 1000


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

    def p_failure(self, period=RelyFuncts.YEAR, drives=1):
        """ probability of drive failure during a period """
        return float(1) - RelyFuncts.Pn(self.fits * drives, period, n=0)

    def loss(self):
        """ amouint of data lost after a drive failure """
        return self.size

    def p_nre(self):
        """ probability of NRE during recovery """
        return 0        # meaningless for a single disk

    def loss_nre(self, objsize=0):
        """ expected data loss due to NRE's during recovery """
        return 0        # meaningless for a single disk

    def corrupted_bytes(self, bytecount, objsize=0):
        """ number of bytes expected to be lost due to NRE """
        return float(self.nre) * bytecount


class EnterpriseDisk(Disk):
    """ Spec'd Enterprise Drive (Seagate Barracuda) """

    def __init__(self, size=2 * TB):
        Disk.__init__(self, size=size, fits=826, nre=1.0e-15,
                    desc="Enterprise drive")


class ConsumerDisk(Disk):
    """ Spec'd Consumer Drive (Seagate Barracuda) """

    def __init__(self, size=2 * TB):
        Disk.__init__(self, size=size, fits=1320, nre=1.0e-14,
                    desc="Consumer drive")


class RealDisk(Disk):
    """ Specs from Schroeders 2007 FAST paper """

    def __init__(self, size=2 * TB):
        Disk.__init__(self, size=size, fits=7800, nre=1.0e-14,
                    desc="real-world disk")
