# Ceph - scalable distributed file system
#
# Copyright (C) Inktank
#
# This is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 2.1, as published by the Free Software
# Foundation.  See file COPYING.
#

"""
basic site reliability model
   incorporating force majeure events and site replacement time
   the modeled unit is a single site
   (and is independent of the underlying storage)
"""

from RelyFuncts import YEAR, Pfail, FitRate, mttf

GiB = 1000000000
TiB = GiB * 1000
PiB = TiB * 1000

DISASTER = FitRate(.001, YEAR)


class Site:

    def __init__(self, fits=DISASTER, rplc=0, size=1 * PiB):
        """ create a site reliability simulation
            fits -- catastrophic site failures per billion hours
            rplc -- how long it will take to replace a failed facility
            size -- amount of data at this site
        """
        self.fits = fits
        self.replace = rplc
        self.size = size
        self.rawsize = size
        if size >= PiB:
            self.description = "Site (%d PB)" % (size / PiB)
        else:
            self.description = "Site (%d TB)" % (size / TiB)

        self.P_drive = 0    # inapplicable
        self.L_drive = 0    # inapplicable
        self.P_nre = 0      # inapplicable
        self.L_nre = 0      # inapplicable
        self.P_rep = 0      # inapplicable
        self.L_rep = 0      # inapplicable

    def compute(self, period=YEAR, mult=1):
        """ probability of survival for an arbitrary object
                period -- time period over which to estimate failures
                mult -- FIT rate multiplier
        """
        self.P_site = float(1) - Pfail(self.fits * mult, period, n=0)
        self.L_site = self.size
        self.dur = 1.0 - self.P_site

    def availability(self):
        """ fraction of the time during which a remote copy is available """
        # if we are ignoring failures, availability is 100%
        if self.fits == 0:
            return 1.0

        # if there is no repair, annual probability of non-failure
        if self.replace == 0:
            return Pfail(self.fits, YEAR, n=0)

        # one minus the time between failures and repair
        ttf = mttf(self.fits)
        return float(ttf) / (ttf + self.replace)
