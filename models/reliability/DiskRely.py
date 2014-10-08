#
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
basic disk reliability model
   the modeled unit is one drive
"""

from RelyFuncts import YEAR, Pfail, Pn

GiB = 1000000000
TiB = GiB * 1000

DISKSIZE = 2 * TiB


class Disk:

    def __init__(self, size, fits, nre, desc, fits2=0):
        """ create a disk reliability simulation
            size -- in bytes
            fits -- failures per billion hours
            nre -- non-recoverable errors per byte
            desc -- description for reporting purposes
            fits2 -- secondary failure rate
        """
        self.size = size
        self.rawsize = size
        self.fits = fits
        self.fits2 = fits if fits2 == 0 else fits2
        self.nre = nre
        self.description = desc

        self.P_rep = 0      # inapplicable
        self.L_rep = 0      # inapplicable
        self.P_site = 0     # inapplicable
        self.L_site = 0     # inapplicable

    def compute(self, period=YEAR, mult=1, secondary=False):
        """ compute probabilities and expected data loss for likely failures
            period -- time over which we want to model failures
            mult -- FIT rate multiplier (e.g. many parallel units)
            secondary -- this is a second (more likely) failure
        """
        fits = self.fits2 if secondary else self.fits
        self.P_drive = float(1) - Pfail(fits * mult, period, n=0)
        self.L_drive = self.size
        self.P_nre = self.p_nre(bytes=self.size * mult)
        self.L_nre = self.size
        self.dur = 1.0 - (self.P_drive + self.P_nre)

    def p_nre(self, bytes=0):
        """ probability of NRE during reading or writing
                bytes -- number of bytes to be written or read
        """
        if bytes == 0:
            bytes = self.size

        # uses a different flavor probability function
        p = Pn(self.nre * bytes * 8, 1)
        return p


class EnterpriseDisk(Disk):
    """ Spec'd Enterprise Drive (Seagate Barracuda) """

    def __init__(self, size=DISKSIZE):
        Disk.__init__(self, size=size, fits=826, nre=1.0e-15,
                      desc="Enterprise drive")


class ConsumerDisk(Disk):
    """ Spec'd Consumer Drive (Seagate Barracuda) """

    def __init__(self, size=DISKSIZE):
        Disk.__init__(self, size=size, fits=1320, nre=1.0e-14,
                      desc="Consumer drive")


class RealDisk(Disk):
    """ Specs from Schroeders 2007 FAST paper """

    def __init__(self, size=DISKSIZE):
        Disk.__init__(self, size=size, fits=7800, nre=1.0e-14,
                      desc="real-world disk")
