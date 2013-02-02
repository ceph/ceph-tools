#
# Multi-site recovery model
#
#   Give models for whole-site RADOS reliability and the probability
#   of force-majeure events that take out an entire site, this model
#   computes the probabilty of losing data that has been replicated
#   across multiple sites (thta are not subject to the same disasters)
#

import RelyFuncts

MB = 1000000
GB = MB * 1000
TB = GB * 1000
PB = TB * 1000


class MultiSite:

    def __init__(self, rados, site, speed=10 * MB, sites=1):
        """ create a site reliability simulation
            rados -- single site rados model
            site -- site model
            speed -- multi-site recovery speed
            sites -- number of sites
        """
        self.rados = rados
        self.site = site
        self.sites = sites
        self.speed = speed
        self.recovery = (rados.disk.size / speed) * RelyFuncts.SECOND
        self.description = "%d-site, %d-cp RADOS" % (sites, rados.copies)

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of losing all copies during a perild """

        # probability of losing all copies at primary site
        p = self.rados.p_failure(period)

        # figure out what fraction of secondary site drives are needed
        drives = self.site.size / self.rados.disk.size
        needed = 1.0 if drives >= self.rados.pgs else \
                    float(self.rados.pgs) / drives

        # probability of losing all copies at secondary site during recovery
        psc = needed * self.rados.p_failure(self.recovery)

        # probability of site failing during recovery
        psf = self.site.p_failure(self.recovery)

        # probability of site having failed prior to recovery
        psd = 1.0 - self.site.availability()

        # probability of losing all copies before recovery completes
        failed = 1
        while failed < self.sites:
            p *= (psc + psd + psf)
            failed += 1

        return p

    def loss(self):
        """ amouint of data lost after a drive failure """
        return self.rados.loss()

    def p_nre(self):
        """ probability of NRE during recovery """
        return 0        # meaningless for a site

    def loss_nre(self, objsize=0):
        """ expected data loss due to NRE's during recovery """
        return 0        # meaningless for a site

    def corrupted_bytes(self, bytecount, objsize=0):
        """ number of bytes expected to be lost due to NRE """
        return 0        # meaningless for a site
