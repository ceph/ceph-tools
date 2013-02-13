#
# basic site reliability model
#
#   the modeled unit is a site
#

import RelyFuncts

M = 1000000
G = M * 1000
T = G * 1000
P = T * 1000

DISASTER = RelyFuncts.BILLION / (1000 * RelyFuncts.YEAR)


class Site:

    def __init__(self, fits=DISASTER, rplc=0, size=1 * P):
        """ create a site reliability simulation
            fits -- catastrophic site failures per billion hours
            rplc -- how long it will take to replace a failed facility
            size -- amount of data at this site
        """
        self.fits = fits
        self.replace = rplc
        self.size = size
        if size >= P:
            self.description = "Site (%d PB)" % (size / P)
        else:
            self.description = "Site (%d TB)" % (size / T)

    def durability(self, period=RelyFuncts.YEAR):
        """ probability of survival for an arbitrary object """
        return RelyFuncts.Pn(self.fits, period, n=0)

    def p_failure(self, period=RelyFuncts.YEAR, mult=1):
        """ probability of catastrophic site failure during a period
                period -- time period over which to estimate failures
                mult -- FIT rate multiplier
        """
        return float(1) - RelyFuncts.Pn(self.fits * mult, period, n=0)

    def availability(self):
        """ fraction of the time during which a remote copy is available """
        # if we are ignoring failures, availability is 100%
        if self.fits == 0:
            return 1.0

        # if there is no repair, annual probability of non-failure
        if self.replace == 0:
            return RelyFuncts.Pn(self.fits, RelyFuncts.YEAR, n=0)

        # one minus the time between failures and repair
        mttf = RelyFuncts.BILLION / self.fits
        return float(mttf) / (mttf + self.replace)

    def loss(self, period=RelyFuncts.YEAR, per=0):
        """ amouint of data lost after a complete site failure
            period -- over which we are calculating loss
            per -- 0 -> site, else size of the farm
        """
        # if we lose it, we lose it all
        return self.size if per == 0 else per

    def p_nre(self):
        """ probability of NRE during recovery """
        return 0        # meaningless for a site

    def loss_nre(self):
        """ expected data loss due to NRE's during recovery """
        return 0        # meaningless for a site

    def corrupted_bytes(self, bytecount):
        """ number of bytes expected to be lost due to NRE """
        return 0        # meaningless for a site
