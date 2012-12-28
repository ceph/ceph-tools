#
# basic disk reliability models
#

import RelyFuncts

MB = 1000000
GB = MB * 1000
TB = GB * 1000
PB = TB * 1000

class Disk:

    def __init__(self, size=2 * TB, fits=826, nre=1.0e-15):
        """ create a disk reliability simulation """
        self.size = size
        self.fits = fits
        self.nre = nre
        self.drives_per_pb = PB / size

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of drive failure during a period """
        return float(1) - RelyFuncts.Pn(self.fits, period, n=0)

    def corrupted_bytes(self, bytecount):
        """ number of bytes expected to be lost due to NRE """
        return float(self.nre) * bytecount




