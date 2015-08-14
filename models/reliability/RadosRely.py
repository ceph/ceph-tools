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
RADOS reliability model
    the modeled unit is a Placement Group
"""

from RelyFuncts import SECOND, MINUTE, YEAR
from sizes import KB, MB, GB

MARKOUT = 10 * MINUTE
RECOVER = 50 * 1000000
FULL = 0.75


class RADOS(object):
    """ model a single-volume RADOS OSD """

    def __init__(self, disk,
                 pg=200,             # recommended
                 copies=2,           # recommended minimum
                 speed=RECOVER,      # typical large object speed
                 delay=MARKOUT,      # default mark-out
                 fullness=FULL,      # how full are the volumes
                 objsize=1 * GB,     # average object size
                 stripe=1,           # typical stripe length
                 nre_model="ignore"):  # scrub largely eliminates these
        """ create a RADOS reliability simulation
            pg -- number of placement groups per OSD
            copies -- number of copies for these objects
            speed -- expected recovery rate (bytes/second)
            delay -- automatic mark-out interval (hours)
            objsize -- typical object size
            stripe -- typical stripe length
            nre_model -- how to handle NREs (ignore, error, fail)
        """
        self.disk = disk
        self.speed = speed
        self.pgs = pg
        self.copies = copies
        self.delay = delay
        self.full = fullness
        self.objsize = objsize
        self.stripe = stripe
        self.nre_model = nre_model
        self.size = disk.size                # useful data
        self.rawsize = disk.size * copies    # space consumed
        self.description = "RADOS: %d cp" % (copies)

        self.P_site = 0     # inapplicable
        self.L_site = 0     # inapplicable
        self.P_rep = 0      # inapplicable
        self.L_rep = 0      # inapplicable

    def rebuild_time(self, speed):
        """ expected time to recover from a drive failure """
        seconds = float(self.disk.size * self.full) / (speed * self.pgs)
        return seconds * SECOND

    def loss_fraction(self, sites=1):
        """ the fraction of objects that are lost when a drive fails """

        if self.copies <= 1 and sites <= 1:
            return 1
        return float(1) / (2 * self.pgs)

    def compute(self, period=YEAR, mult=1):
        """ probability of an arbitrary object surviving the period
                period -- time over which Pfail should be estimated
                mult -- FIT rate multiplier
        """
        self.dur = 1.0

        # probability of an initial failure (of any copy)
        n = mult * self.copies * self.stripe
        self.disk.compute(period=period, mult=n)
        self.P_drive = self.disk.P_drive
        self.P_nre = self.disk.P_drive

        # probability of losing the remaining copies
        n = self.pgs
        recover = float(self.delay) + self.rebuild_time(self.speed)
        copies = self.copies - 1
        while copies > 0:
            self.disk.compute(period=recover, mult=copies * n,
                              secondary=True)
            self.P_drive *= self.disk.P_drive
            if copies > 1:
                self.P_nre *= self.disk.P_drive
            copies -= 1

        # amount of data to be read and written
        read_bytes = self.size * self.full
        write_bytes = read_bytes if self.copies > 1 else 0

        # fraction of objects affected by this failure
        fraction = self.loss_fraction()
        self.L_drive = read_bytes * fraction
        self.dur = 1.0 - (self.P_drive * fraction)

        # probability of and expected loss due to NREs
        if self.nre_model == "ignore":
            self.P_nre = 0
            self.L_nre = 0
        else:       # we will lose the lesser of a PG or object
            self.P_nre *= self.disk.p_nre(bytes=read_bytes + write_bytes)
            pg = self.size * self.full * fraction
            self.L_nre = self.objsize if self.objsize < pg else pg
            self.dur -= self.P_nre * self.L_nre / (self.size * self.full)
