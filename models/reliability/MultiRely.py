#
# Multi-site recovery model
#
#   the modeled unit is, again, a Placement Group, but now we factor
#   in multi-site replication, force majeure events and site repairs.
#
#   This makes all of the functions in this module more complex than
#   their single-site counterparts, because they factor in combinations
#   of device and site failures
#

import RelyFuncts

M = 1000000


class MultiSite:

    def __init__(self, rados, site, speed=10 * M, latency=0, sites=1):
        """ create a site reliability simulation
            rados -- single site rados model
            site -- site model
            speed -- multi-site replication/recovery speed
            latency -- replication latency
            sites -- number of sites
        """
        self.rados = rados
        self.site = site
        self.sites = sites
        self.speed = speed
        self.recovery = (rados.disk.size / speed) * RelyFuncts.SECOND
        self.latency = latency
        self.size = site.size   # size of each site
        self.description = "RADOS: %d-site, %d-cp" % (sites, rados.copies)

    def compute(self, period=RelyFuncts.YEAR):
        """ compute the probabilities of each type of failure """

        # probability of losing a first site or all of its copies
        self.ppf = self.site.p_failure(period, mult=self.sites)
        self.ppc = self.rados.p_failure(period, mult=self.sites)

        # probability (non-trivial) of remote site being down when we need it
        self.psd = 1.0 - self.site.availability()

        # probability (low) of losing all secondary copies during recovery
        drives = self.site.size / self.rados.disk.size
        needed = 1.0 if drives >= self.rados.pgs else \
                    float(self.rados.pgs) / drives
        # FIX this is what we need from second site, but it is less for third
        self.psc = self.rados.p_failure(self.recovery, mult=needed)

        # probability (negligible) of site failing during recovery
        self.psf = self.site.p_failure(self.recovery)

        # probability of losing all backup copies before we can recover
        self.multifail = 1                  # given we have lost primary copies
        failed = 1
        while failed < self.sites:
            self.multifail *= (self.psc + self.psd + self.psf)
            failed += 1

    def durability(self, period=RelyFuncts.YEAR):
        """ probability of survival of an arbitrary object """

        # figure out the probabilities
        self.compute(period=period)

        # primary site and all copies fail ... every object lost
        Pf = self.ppf * self.multifail

        # primary and all other copies fail ... probably 1/2 Placement Group
        mult = self.sites * self.rados.obj_stripe()
        Pc = self.rados.p_failure(period, mult=mult) * self.multifail
        Pc *= self.rados.loss_fraction(sites=self.sites)

        # failure to replicate loses work in transit
        if self.latency > 0:
            Pr = self.ppf
            # BOGOSITY ALERT!!! ... fraction of objects affected
            Pr *= RelyFuncts.SECOND * period * self.speed \
                 / (self.site.size * 2)
        else:
            Pr = 0

        return float(1) - (Pf + Pc + Pr)

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of losing all copies during a perild """

        # figure out the probabilities
        self.compute(period=period)

        # if there is only one site, this is simple
        if self.sites < 2:
            return self.ppf + self.ppc

        # do we have to deal with pre-replication failures
        #    if so, primary site failures are total failures
        if self.latency > 0:
            return self.ppf + (self.ppc * self.multifail)
        else:
            return (self.ppf + self.ppc) * self.multifail

    #
    # this is more complex than any of the other loss functions
    # because multi-site includes different types of failures
    #
    def loss(self, period=RelyFuncts.YEAR, per=0):
        """ amouint of data lost after failure
            period -- over which we are calculating loss
            per -- 0 -> single incident, else size of the farm
        """
        # figure out the probabilities
        self.compute(period=period)

        # expected loss from complete site failures
        Ls = self.site.loss(period=period, per=per)
        if per > 0:
            Ls *= float(per) / (self.site.size * self.sites)
        Ps = self.ppf * (self.psf ** (self.sites - 1))

        # expected loss from failures of copies
        Lc = self.rados.disk.size * self.rados.full * \
             self.rados.loss_fraction(sites=self.sites)
        if per > 0:
            Lc *= per / (self.rados.disk.size * self.rados.copies * self.sites)
        Pc = (self.ppf + self.ppc) * self.multifail

        # expected data loss from not-yet-replicated data
        Lr = RelyFuncts.SECOND * self.latency * self.speed / 2
        Pr = self.ppf

        # return the probability weighted loss
        return ((Ps * Ls) + (Pc * Lc) + (Pr * Lr)) / (Ps + Pc + Pr)

    def p_nre(self):
        """ probability of NRE during recovery """
        return 0        # meaningless for a site

    def loss_nre(self, period=RelyFuncts.YEAR):
        """ expected data loss due to NRE's during recovery """
        return 0        # meaningless for a site

    def corrupted_bytes(self, bytecount):
        """ number of bytes expected to be lost due to NRE """
        return 0        # meaningless for a site
