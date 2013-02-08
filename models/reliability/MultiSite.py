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

    def __init__(self, rados, site, speed=10 * MB,
                latency=5 * RelyFuncts.MINUTE, sites=1):
        """ create a site reliability simulation
            rados -- single site rados model
            site -- site model
            speed -- multi-site recovery speed
            latency -- replication latency
            sites -- number of sites
        """
        self.rados = rados
        self.site = site
        self.sites = sites
        self.speed = speed
        self.recovery = (rados.disk.size / speed) * RelyFuncts.SECOND
        self.latency = latency
        self.description = "RADOS: %d-site, %d-cp" % (sites, rados.copies)
        self.pSite = .5     # fix this in p_failure
        self.pDrive = .5    # fix this in p_failure

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of losing all copies during a perild """

        # probability of losing all copies at primary site
        p = self.rados.p_failure(period)
        if self.sites == 1:
            return p + (1.0 - self.site.availability())

        # figure out what fraction of secondary site drives are needed
        drives = self.site.size / self.rados.disk.size
        needed = 1.0 if drives >= self.rados.pgs else \
                    float(self.rados.pgs) / drives

        # probability (non-trivial) of remote site being down when we need it
        psd = 1.0 - self.site.availability()

        # probability (low) of losing all secondary copies during recovery
        psc = needed * self.rados.p_failure(self.recovery)

        # probability (negligible) of site failing during recovery
        psf = self.site.p_failure(self.recovery)

        # EVIL side effects ... save these probabilities for loss()
        self.pSite = (psf + psd) / (psc + psf + psd)
        self.pDrive = 1 - self.pSite

        # probability of losing all copies before recovery completes
        failed = 1
        while failed < self.sites:
            p *= (psc + psd + psf)
            failed += 1

        # probability (negligible) of losing the primary before it replicates
        p += self.site.p_failure(self.latency)
        return p

    def loss(self):
        """ amouint of data lost after a drive failure """

        # if the whole site goes down, we lose everything
        lSite = self.rados.loss()

        # if only a single drive goes down, it is more complicated
        #     if there is only one copy per site, the rados simulation
        #     did not factor in declustered reocovery
        lDrive = lSite
        if self.rados.copies == 1:
            lDrive /= 2                # failure happens mid-recovery
            lDrive /= self.rados.pgs   # declustering limits data lost

        # return the weighted average
        return (self.pSite * lSite) + (self.pDrive * lDrive)

    def p_nre(self):
        """ probability of NRE during recovery """
        return 0        # meaningless for a site

    def loss_nre(self, objsize=0):
        """ expected data loss due to NRE's during recovery """
        return 0        # meaningless for a site

    def corrupted_bytes(self, bytecount, objsize=0):
        """ number of bytes expected to be lost due to NRE """
        return 0        # meaningless for a site
