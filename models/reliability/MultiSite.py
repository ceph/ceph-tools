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

    def __init__(self, rados, site, speed=10 * MB, latency=0, sites=1):
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
        self.description = "RADOS: %d-site, %d-cp" % (sites, rados.copies)
        self.pSite = .5     # WARNING: set in p_failure, used in p_loss
        self.pDrive = .5    # WARNING: set in p_failure, used in p_loss
        self.pRep = 0.0     # WARNING: set in p_failure, used in p_loss

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of losing all copies during a perild """

        # probability of losing the primary site or all of its copies
        ppf = self.site.p_failure(period)       # primary site failure
        ppc = self.rados.p_failure(period)      # primary loses all copies

        # figure out what fraction of secondary site drives are needed
        drives = self.site.size / self.rados.disk.size
        needed = 1.0 if drives >= self.rados.pgs else \
                    float(self.rados.pgs) / drives

        # probability (non-trivial) of remote site being down when we need it
        psd = 1.0 - self.site.availability()

        # probability (low) of losing all secondary copies during recovery
        #   (should be needed * FIT rate, but they are very close)
        psc = needed * self.rados.p_failure(self.recovery)

        # probability (negligible) of site failing during recovery
        psf = self.site.p_failure(self.recovery)

        # probability of losing all backup copies before we can recover
        multifail = 1                       # given we have lost primary copies
        failed = 1
        while failed < self.sites:
            multifail *= (psc + psd + psf)  # secondary loses all of its copies
            failed += 1

        # if there is only one site, this is simple
        if self.sites < 2:
            tot = ppf + ppc
            self.pSite = ppf / tot
            self.pDrive = ppc / tot
            self.pRep = 0
            return tot

        # denominator for weighted data loss computation
        tot = ppf + ppc + psf + psd + psc

        # consider pre-replication primary site failures
        if self.latency > 0:
            self.pSite = (psf + psd) / tot
            self.pDrive = (ppc + psc) / tot
            self.pRep = ppc / tot
            return ppf + (ppc * multifail)

        # all failures are post-replication
        self.pSite = (ppf + psf + psd) / tot
        self.pDrive = (ppc + psc) / tot
        self.pRep = 0
        return (ppf + ppc) * multifail

    def loss(self):
        """ amouint of data lost after a drive failure """

        # if a whole site goes down, we lose everything on the disk
        l = self.pSite * self.rados.loss()

        # if only a single drive goes down, it is more complicated
        #     if there is only one copy per site, the rados simulation
        #     did not factor in declustered reocovery
        lDrive = self.rados.loss()
        if self.rados.copies == 1:
            lDrive /= 2                # failure happens mid-recovery
            lDrive /= self.rados.pgs   # declustering limits data lost
        l += self.pDrive * lDrive

        # if the problem is failure to replicate, we loose work-in-transit
        lostBytes = self.speed * self.speed / RelyFuncts.SECOND
        l += self.pRep * lostBytes

        # return the weighted average data loss
        return l

    def p_nre(self):
        """ probability of NRE during recovery """
        return 0        # meaningless for a site

    def loss_nre(self, objsize=0):
        """ expected data loss due to NRE's during recovery """
        return 0        # meaningless for a site

    def corrupted_bytes(self, bytecount, objsize=0):
        """ number of bytes expected to be lost due to NRE """
        return 0        # meaningless for a site
