#
# basic disk reliability models
#
#   FITS: failures per billion hours
#   NRE: expected non-recoverable (detected or not) errors/byte read

import RelyFuncts

MB = 1000000
GB = MB * 1000
TB = GB * 1000
PB = TB * 1000


class Disk:

    def __init__(self, size, fits, nre):
        """ create a disk reliability simulation """
        self.size = size
        self.fits = fits
        self.nre = nre
        self.drives_per_pb = float(PB) / size

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of drive failure during a period """
        return float(1) - RelyFuncts.Pn(self.fits, period, n=0)

    def loss(self):
        """ amouint of data lost after a drive failure """
        return self.size

    def corrupted_bytes(self, bytecount):
        """ number of bytes expected to be lost due to NRE """
        return float(self.nre) * bytecount


class EnterpriseDisk(Disk):
    """ Spec'd Enterprise Drive (Seagate Barracuda) """

    def __init__(self, size=2 * TB):
        Disk.__init__(self, size=size, fits=826, nre=1.0e-15)
        self.description = "Enterprise drive"


class ConsumerDisk(Disk):
    """ Spec'd Consumer Drive (Seagate Barracuda) """

    def __init__(self, size=2 * TB):
        Disk.__init__(self, size=size, fits=1320, nre=1.0e-14)
        self.description = "Consumer drive"


class RealDisk(Disk):
    """ Specs from Schroeders 2007 FAST paper """

    def __init__(self, size=2 * TB):
        Disk.__init__(self, size=size, fits=7800, nre=1.0e-14)
        self.description = "real-world drive"
