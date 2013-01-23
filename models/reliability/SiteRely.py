#
# basic site reliability model
#

import RelyFuncts

MB = 1000000
GB = MB * 1000
TB = GB * 1000
PB = TB * 1000


class Site:

    def __init__(self, fits, speed=1 * MB,
                repair=RelyFuncts.YEAR, size=1 * PB, sites=1):
        """ create a site reliability simulation
            fits -- catastrophic site failures per billion hours
            speed -- remote data recovery speed
            repair -- site replacements per billion hours
            size -- amount of data at this site
            sites -- number of sites
        """
        self.sites = sites
        self.fits = fits
        self.speed = speed
        self.repair = repair
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
        return float(1) - float(self.fits) / self.repair

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
