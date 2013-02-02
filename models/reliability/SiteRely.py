#
# basic site reliability model
#

import RelyFuncts

MB = 1000000
GB = MB * 1000
TB = GB * 1000
PB = TB * 1000

DISASTER = RelyFuncts.BILLION / (1000 * RelyFuncts.YEAR)


class Site:

    def __init__(self, fits=DISASTER, avail=0.99, size=1 * PB):
        """ create a site reliability simulation
            fits -- catastrophic site failures per billion hours
            avail -- long term site availability (including replacement)
            size -- amount of data at this site
        """
        self.fits = fits
        self.avail = avail
        self.size = size
        if size >= PB:
            self.description = "Site (%d PB)" % (size / PB)
        else:
            self.description = "Site (%d TB)" % (size / TB)

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of catastrophic site failure during a period """
        return float(1) - RelyFuncts.Pn(self.fits, period, n=0)

    def availability(self):
        """ fraction of the time during which a remote copy is available """
        return self.avail

    def loss(self):
        """ amouint of data lost after a drive failure """
        return self.size

    def p_nre(self):
        """ probability of NRE during recovery """
        return 0        # meaningless for a site

    def loss_nre(self, objsize=0):
        """ expected data loss due to NRE's during recovery """
        return 0        # meaningless for a site

    def corrupted_bytes(self, bytecount, objsize=0):
        """ number of bytes expected to be lost due to NRE """
        return 0        # meaningless for a site
