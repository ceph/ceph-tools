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
Multi-site recovery model

   the modeled unit is, again, a Placement Group, but now we factor
   in multi-site replication, force majeure events and site repairs.

   This makes all of the functions in this module more complex than
   their single-site counterparts, because they factor in combinations
   of device and site failures
"""

from RelyFuncts import SECOND, YEAR

MiB = 1000000


class MultiSite(object):

    def __init__(self, rados, site, speed=10 * MiB, latency=0, sites=1):
        """ create a site reliability simulation
            rados -- single site rados reliability model
            site -- site reliability model
            speed -- multi-site replication/recovery speed
            latency -- replication latency
            sites -- number of sites replicating a single object
        """
        self.rados = rados
        self.site = site
        self.sites = sites
        self.speed = speed
        self.latency = latency
        self.size = site.size   # useful size of each site
        self.rawsize = site.size * sites
        self.description = "RADOS: %d-site, %d-cp" % (sites, rados.copies)

    def descend(self, period, p, f, survivors):
        """ recursive per site failure model
            period -- the period during which this site must remain up
            p -- accumulated probability of reaching this point
            f -- tupple of accumulated failures thus far
                 (sites, all copies on site, NREs)
            survivors -- number of surviving replica sites
        """

        # probabilities of site or copy failures during period
        self.site.compute(period=period, mult=survivors)
        self.rados.compute(period=period)
        if survivors > 1:
            # we haven't yet reached the bottom of the tree
            self.descend(self.site.replace, p * self.site.P_site,
                         (f[0] + 1, f[1], f[2]), survivors - 1)
            self.descend(self.rados.rebuild_time(self.speed),
                         p * self.rados.P_drive,
                         (f[0], f[1] + 1, f[2]), survivors - 1)
            obj_fetch = SECOND * self.rados.objsize / self.speed
            self.descend(obj_fetch, p * self.rados.P_nre,
                         (f[0], f[1], f[2] + 1), survivors - 1)
            return

        # we are down to the last site
        if f[0] + f[1] == self.sites - 1:   # these are last copies
            self.P_drive += p * self.rados.P_drive
            self.L_drive = self.rados.L_drive   # sb 1/2 PG
            self.P_nre += p * self.rados.P_nre      # FIX ... wrong bytecount
            self.L_nre = self.rados.L_nre           # sb one object
            if f[0] == self.sites - 1:      # this is last site
                self.P_site += p * self.site.P_site
                self.L_site = self.site.L_site

    def compute(self, period=YEAR, mult=1):
        """ compute the failure tree for multiple sites """

        # initialize probabilities
        self.dur = 1.0
        self.P_site = 0
        self.P_drive = 0
        self.P_nre = 0
        self.P_rep = 0
        self.L_rep = 0
        self.L_nre = 0
        self.L_drive = 0
        self.L_site = 0

        # note a few important sizes
        disk_size = self.rados.size * self.rados.full
        pg_size = disk_size / self.rados.pgs

        # descend the tree of probabilities and tally the damage
        self.descend(period=period, p=1.0, f=(0, 0, 0), survivors=self.sites)

        # compute the probability/loss for asynchronous replication failure
        if self.latency > 0:
            self.site.compute(period=YEAR, mult=self.sites)
            self.P_rep = self.site.P_site
            self.L_rep = self.latency * self.speed / (2 * SECOND)

        # compute the (loss weighted) overall multi-site durability
        self.dur -= self.P_site
        self.dur -= self.P_drive * self.L_drive / disk_size
        self.dur -= self.P_nre * self.L_nre / disk_size
        self.dur -= self.P_rep * self.L_rep / disk_size
