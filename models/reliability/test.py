#!/usr/bin/python
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
unit test exerciser

    I can't claim to know what the "correct" answers are to any
    realiability simulation, as few calculators agree on anything
    but the simplest of problems.

    But it turns out that very crude estimates (doing simple
    addition and multiplication) yield results that are pretty
    close to the correct ones.  Thus I can create crude/simple
    models, and then confirm that the (very differently implemented)
    real models produce results in the same ballpark (often within
    less than 1%)

    This does not check my fundamental understanding of how
    to model various situations, but it does check that the
    complex code and math are correctly implementing the
    intended modeling (and it has found such mistakes).

    If you want to understand the models, look at how these
    test cases compute the "exp" (expected) values.  If any
    of those seem wrong, that is interesting.

    Hopefully this code has been written so that (modulo slop margins)
    you can tweek any test parameter values and the expected value
    computations will adjust to them.

 NOTES:
    To avoid the compounding of estimation errors, I regularly
    replace estimated values with (presumably more accurate)
    modeled values AFTER having validated their reasonablness.
    This greatly reduces the allowed slop in compound probabilities.

    Another source of slop is harder to control for.  Multipliying
    a proability to approximate the probability of events from
    multiple sources breaks down as the probabilities and/or
    multiples get higher ... and this is the source of most of
    the wide (>1%) slop margins.

 TODO
    look for outside results I can compare with
"""

from RelyFuncts import SECOND, YEAR
from DiskRely import Disk
from RaidRely import RAID0, RAID1, RAID5, RAID6
from RadosRely import RADOS
from SiteRely import Site
from MultiRely import MultiSite


def approximates(v1, v2, slop=0.005):
    """ determine whether or not two values are very nearly equal
        v1 -- value to be checked
        v2 -- expected value
        slop -- acceptable deviation (as a fraction of v2)
    """
    return v1 <= v2 * (1.0 + slop) and v1 >= v2 * (1.0 - slop)


class Test:

    def __init__(self):

        # statistics to be collected
        self.passed = 0
        self.failed = 0
        self.notyet = 0

        # standard test parameters
        #
        #   Note, it does not matter whether or not these values
        #   are representative of particular systems, as they are
        #   only used as test parameters to drive the results of
        #   sanity tests
        #
        self.size = 1000000000000   # DISK size
        self.fits = 826             # DISK FITS
        self.nre = 1.0E-15          # DISK NRE

        self.recovery = 100000000   # RADOS recovery b/w (per osd))
        self.objsize = 1000000      # RADOS object size
        self.pgs = 100              # RADOS declustering factor
        self.full = 0.75            # RADOS how full we keep file systems
        self.stripe = 8             # RADOS how many objects per stripe

        self.s_fits = 1000          # site failure rate
        self.s_recovery = 15000000  # multi-site recovery b/w (per site)
        self.s_replace = 20 * 24    # hours to replace a destroyed site
        self.s_latency = 1.0 / 60   # hours replication latency
        self.s_size = 2000000000000000  # site size (2PiB)

    def test(self, testid, desc, val, expected, slop=0.005):
        """ compare two values and record sucess/failure
            testid -- identification tag for this test
            desc -- description of the test
            val -- result to be checked
            expected -- expected value
            slop -- acceptable slop (-1 means not yet implemented)
        """
        if slop < 0:
            self.notyet += 1
            return False
        elif approximates(val, expected, slop):
            self.passed += 1
            return True
        else:
            print("FAIL %s (%s): val=%e, exp=%e, slop=%f" %
                  (testid, desc, val, expected, slop))
            self.failed += 1
            return False

    #
    # Disk Reliability test suite
    #
    def diskTest(self):
        """ sanity check the DiskRely simulation """

        # ball-park expected results
        Pfail = float(self.fits) * YEAR / 1000000000
        Pnre = self.nre * self.size * 8

        # a basic reliability calculation with a known outcome
        e_disk = Disk(size=self.size, fits=self.fits, nre=self.nre,
                      desc="test")
        e_disk.compute(period=YEAR, mult=1)
        v = e_disk.P_drive
        exp = Pfail
        if self.test("1A", "PFail(1 drive)", v, exp):
            Pfail = e_disk.P_drive      # move to validated result

        # driver failure loses entire drive
        v = e_disk.L_drive
        exp = self.size
        self.test("1B", "L(drive)", v, exp)

        # NRE's roughly match amount of data transferred
        exp = self.nre * self.size * 8
        v = e_disk.P_nre
        self.test("1C", "Pnre(1 drive)", v, exp, slop=0.01)

        # one year durability
        v = 1.0 - e_disk.dur    # complement for better precision
        exp = (Pfail + (self.nre * self.size * 8))
        self.test("1D", "Durability(1 drive)", v, exp)

        # 2x mullt-> 2x Pfail
        e_disk.compute(period=YEAR, mult=2)
        v = e_disk.P_drive
        exp = 2 * Pfail
        self.test("1E", "PFail(2 drives)", v, exp)

        # NRE loses entire drive
        exp = self.size
        v = e_disk.L_nre
        self.test("1F", "Lnre(2 drives)", v, exp)

        # 2x time-> 2x Pfail
        e_disk.compute(period=2 * YEAR)
        v = e_disk.P_drive
        exp = 2 * Pfail
        self.test("1G", "PFdrive(period=2y)", v, exp)

        # two year durability
        v = 1.0 - e_disk.dur    # complement for better precision
        exp = ((2 * Pfail) + (self.nre * self.size * 8))
        self.test("1H", "Durability(2 drive)", v, exp, slop=.01)

        # raw size = volume size
        v = e_disk.rawsize
        exp = self.size
        self.test("1Z", "raw size", v, exp)

    #
    # RAID Reliability test suite
    #
    def raidTest(self):
        """ sanity check the RaidRely simulation """

        e_disk = Disk(size=self.size, fits=self.fits, nre=self.nre,
                      desc="test")

        # ballpark expected results for single disk error rates
        Pfail = float(self.fits) * YEAR / 1000000000
        Pnre = self.nre * self.size * 8         # pnre during recovery

        # Sanity check one-disk RAID vs one disk, and get better estimates
        raidnone = RAID0(e_disk, volumes=1, delay=0, recovery=0,
                         nre_model="fail", objsize=self.objsize)
        raidnone.compute(period=YEAR)
        exp = Pfail
        v = raidnone.P_drive
        if self.test("2A", "PFdrive(raid0,1) == PFdrive(disks)", v, exp):
            Pfail = raidnone.P_drive        # move to more accurate value

        # Sanity check one-disk RAID vs one disk, and get better estimates
        exp = Pnre
        v = raidnone.P_nre
        if self.test("2B", "Pnre(raid0,1) == Pnre(disks)", v, exp, slop=0.01):
            Pnre = raidnone.P_nre

        # single volume durability
        v = 1.0 - raidnone.dur      # complement for better precision
        exp = Pfail + Pnre
        self.test("2C", "Durability(raid0,1)", v, exp)

        # raw size = volume size
        v = raidnone.rawsize
        exp = self.size
        self.test("2D", "RAID0 x1 raw size", v, exp)

        # RAID-0 two-volume P_fail vs that of disk
        raid0 = RAID0(e_disk, volumes=2, delay=0, recovery=0,
                      nre_model="fail", objsize=self.objsize)
        raid0.compute(period=YEAR)
        exp = 2 * Pfail     # 2 volumes, twice the p_fail
        v = raid0.P_drive
        self.test("2E", "PFdrive(raid0,2) vs PFdrive(2 disks)", v, exp)

        # RAID-0 NRE
        PnreX2 = 2 * Pnre    # 2 volumes, (very crudely) twice the NREs
        exp = PnreX2
        v = raid0.P_nre
        if self.test("2F", "Pnre(raid0,2) vs Pnre(2 dsk)", v, exp, slop=0.01):
            PnreX2 = raid0.P_nre             # move to more accurate value

        # two volume durability
        v = 1.0 - raid0.dur         # complement for better precision
        exp = (2 * Pfail) + PnreX2
        self.test("2G", "Durability(raid0,2)", v, exp)

        # raw size = volume size
        v = raid0.rawsize
        exp = 2 * self.size
        self.test("2H", "RAID0 x2 raw size", v, exp)

        # ballpark expected results for two disk error rates
        Tr = float(self.size / self.recovery) / 3600      # recovery time
        Pfail2 = Pfail * Tr / YEAR  # probability of failure during recovery

        # RAID-1 two volume P_fail vs that of disk
        raid1 = RAID1(e_disk, volumes=2, delay=0,
                      recovery=self.recovery, nre_model="fail",
                      objsize=self.objsize)
        raid1.compute(period=YEAR)
        exp = 2 * Pfail * Pfail2            # 1of2, 1of1
        v = raid1.P_drive
        if self.test("2I", "PFdrive(raid1,2) vs PFdrive(disks)", v, exp):
            Pfail2 = raid1.P_drive / (2 * Pfail)  # move to more accurate value

        # RAID-1 NRE
        exp = 2 * Pfail * PnreX2         # 1of2, read, write
        v = raid1.P_nre
        self.test("2J", "Pnre(raid1,2) vs Pnre(2 disks)", v, exp)

        # two volume durability
        v = 1.0 - raid1.dur         # complement for better precision
        exp = (2 * Pfail * Pfail2) + (2 * Pfail * PnreX2)
        self.test("2K", "Durability(raid1,2)", v, exp)

        # raw size = 2 volume size
        v = raid1.rawsize
        exp = 2 * self.size
        self.test("2L", "RAID1 (1+1) raw size", v, exp)

        # RAID-5 three volume P_fail vs that of disk
        raid5 = RAID5(e_disk, volumes=3, delay=0,
                      recovery=self.recovery,
                      nre_model="fail",
                      objsize=self.objsize)
        raid5.compute(period=YEAR)
        exp = (3 * Pfail) * (2 * Pfail2)    # 1of3, 1of2
        v = raid5.P_drive
        self.test("2M", "PFdrive(raid5,3) vs 2/3 disks", v, exp)

        # Raid5 three volume durability
        v = 1.0 - raid5.dur         # complement for better precision
        exp = (3 * Pfail) * (2 * Pfail2)    # 1of3, 1of2
        exp += (3 * Pfail) * (1.5 * PnreX2)
        self.test("2N", "Durability(raid5,3)", v, exp, slop=0.02)

        # raw size = 3 volume size
        v = raid5.rawsize
        exp = 3 * self.size
        self.test("2O", "RAID5 (2+1) raw size", v, exp)

        # RAID-5 four volume P_fail vs that of disk
        raid5a = RAID5(e_disk, volumes=4, delay=0,
                       recovery=self.recovery,
                       nre_model="fail", objsize=self.objsize)
        raid5a.compute(period=YEAR)
        exp = (4 * Pfail) * (3 * Pfail2)    # 1of4, 1of3
        v = raid5a.P_drive
        self.test("2P", "PFdrive(raid5,4) vs 2/4 disks", v, exp, slop=0.01)

        # RAID-5 NRE
        Pnrex4 = 2 * PnreX2
        exp = (4 * Pfail) * Pnrex4     # one of four fails, read 3, write 1
        v = raid5a.P_nre
        if self.test("2Q", "Pnre(raid5,4) vs Pnre(4 dsk)", v, exp, slop=0.03):
            Pnrex4 = raid5a.P_nre / (4 * Pfail)  # move to more accurate value

        # Raid5 five volume durability
        v = 1.0 - raid5a.dur
        exp = (4 * Pfail) * (3 * Pfail2)
        exp += (4 * Pfail) * Pnrex4
        self.test("2R", "Durability(raid5,4)", v, exp)

        # raw size = 3 volume size
        v = raid5a.rawsize
        exp = 4 * self.size
        self.test("2S", "RAID5 (4+1) raw size", v, exp)

        # ballpark estimate for three drive
        Pfail3 = 3 * Pfail * 2 * Pfail2 * Pfail2    # 1of3, 1of2, 1of1

        # RAID-6 four volume P_fail vs that of disk
        raid6 = RAID6(e_disk, volumes=4, delay=0,
                      recovery=self.recovery,
                      nre_model="fail", objsize=self.objsize)
        raid6.compute(period=YEAR)
        exp = 4 * Pfail3                # 1of4 (1of3, 1of2)
        v = raid6.P_drive
        if self.test("2T", "PFdrive(raid6,4) vs PFdrive(3/4 disks)", v, exp):
            Pfail3 = raid6.P_drive / 4      # move to more accurate value

        # RAID-6 six volume P_fail vs that of disk
        raid6a = RAID6(e_disk, volumes=6, delay=0,
                       recovery=self.recovery,
                       nre_model="fail", objsize=self.objsize)
        raid6a.compute(period=YEAR)
        exp = 5 * 4 * Pfail3            # 1of6, 1of5, 1of4
        v = raid6a.P_drive
        self.test("2U", "PFdrive(raid6,6) vs PFdrive(3/6 disks)", v, exp,
                  slop=0.01)

        # RAID-6 NRE
        PnreX5 = 5 * Pnrex4 / 4
        exp = (6 * Pfail) * (5 * Pfail2) * PnreX5  # 1of6, 1of5, rd4, wrt 1
        v = raid6a.P_nre
        self.test("2V", "Pnre(RAID6,6) vs Pnre(6 disks)", v, exp, slop=0.02)

        # RAID-6 NRE data lost
        exp = 4 * self.size                         # lose 4 vols of data
        v = raid6a.L_nre
        self.test("2W", "Lnre(Raid6,6) vs Lnre(4 disks)", v, exp)

        # Raid6 six volume durability
        v = 1.0 - raid6a.dur    # complement for improved precision
        exp = 5 * 4 * Pfail3
        exp += (6 * Pfail) * (5 * Pfail2) * PnreX5
        self.test("2X", "Durability(raid6,6)", v, exp, slop=0.02)

        # raw size = 3 volume size
        v = raid6a.rawsize
        exp = 6 * self.size
        self.test("2Y", "RAID6(4+2) raw size", v, exp)

        # RAID-6 NRE=error, Pnre
        raid6a.nre_model = "error"
        raid6a.compute(period=YEAR)
        exp = (6 * Pfail) * (5 * Pfail2) * PnreX5  # 1of6, 1of5, rd4, wrt1
        v = raid6a.P_nre
        self.test("2Z", "Pnre(raid6,6) vs Pnre(4 disks)", v, exp, slop=0.02)

        # RAID-6 NRE=error, data lost
        exp = self.objsize                          # one NRE, lose one obj
        v = raid6a.L_nre
        self.test("2AA", "Lnre(raid6,4) vs objsize", v, exp)

        # RAID-6 NRE=ignore
        raid6a.nre_model = "ignore"                 # ignore -> no errors/loss
        raid6a.compute(period=YEAR)
        v = raid6a.L_nre
        exp = 0
        self.test("2AB", "nre=ignore, Lnre=0", v, exp)

        # A RAID-6 NRE=ignore
        raid6a.nre_model = "ignore"                 # ignore -> no errors/loss
        raid6a.compute(period=YEAR)
        v = raid6a.P_nre
        exp = 0
        self.test("2AC", "nre=ignore, Pnre=0", v, exp)

        # add delay equal to recovery, Pfail *=2
        raid1.delay = Tr
        raid1.compute(period=YEAR)
        exp = 2 * (2 * Pfail) * Pfail2    # double the previous risk
        v = raid1.P_drive
        self.test("2AD", "delay=recovery, Pfail*=2", v, exp)

        # recovery speed /=2, Pfail *=2
        raid1.speed /= 2
        raid1.delay = 0
        raid1.compute(period=YEAR)
        v = raid1.P_drive
        self.test("2AE", "recovery speed/2, Pfail*=2", v, exp)

    #
    # RADOS Reliability test suite
    #
    def radosTest(self):
        """ sanity check the RadosRely simulation """

        # ballpark expected results
        Pfail = float(self.fits) * YEAR / 1000000000
        Pnre = self.nre * self.full * self.size * 8

        e_disk = Disk(size=self.size, fits=self.fits, nre=self.nre,
                      desc="test")

        # sanity check and calibration RADOS 1cp P_drive vs bare disk
        rados1 = RADOS(e_disk, pg=self.pgs, speed=self.recovery,
                       nre_model="fail", fullness=self.full,
                       objsize=self.objsize, delay=0, stripe=1, copies=1)
        rados1.compute(period=YEAR)
        v = rados1.P_drive
        exp = Pfail
        if self.test("3A", "PFdrive(rados,1cp) = PFdrive(disk)", v, exp):
            Pfail = rados1.P_drive      # move to more accurate value

        # sanity check and calibration RADOS 1cp P_drive vs bare disk
        v = rados1.P_nre
        exp = Pfail * Pnre
        if self.test("3B", "Pnre(rados,1cp) = Pnre(disk)", v, exp, slop=0.01):
            Pnre = rados1.P_nre / Pfail  # move to more accurate value

        # RADOS 1cp L_drive vs bare disk
        exp = self.size * self.full
        v = rados1.L_drive
        self.test("3C", "Ldrive(rados,1cp) = size*full", v, exp)

        # RADOS 1cp durability
        v = 1.0 - rados1.dur        # complement for improved precsision
        exp = Pfail + (Pfail * Pnre)
        self.test("3D", "Durability(rados,1cp)", v, exp, slop=0.01)

        # RADOS 1cp size
        v = rados1.rawsize
        exp = self.size
        self.test("3E", "RADOS 1cp raw size", v, exp)

        # ball park two drive failures
        Tr = float(self.full) * self.size / (self.recovery * self.pgs * 3600)
        Pfail2 = Pfail * self.pgs * Tr / YEAR

        # RADOS 2cp P_drive vs bare disk
        rados2 = RADOS(e_disk, pg=self.pgs, speed=self.recovery,
                       nre_model="fail", fullness=self.full,
                       objsize=self.objsize, delay=0, stripe=1, copies=2)
        rados2.compute(period=YEAR)
        v = rados2.P_drive
        exp = 2 * Pfail * Pfail2
        if self.test("3F", "PFdrive(rados,2cp) = PFdrive(2 disks)", v, exp):
            Pfail2 = rados2.P_drive / (2 * Pfail)   # more accurate value

        # RADOS 2cp L_drive vs bare disk
        exp = self.size * self.full / (2 * self.pgs)
        v = rados2.L_drive
        self.test("3G", "Ldrive(rados,2cp) = size*full/1pg", v, exp)

        # RADOS 2cp durability
        v = 1.0 - rados2.dur    # complement for extra precision
        exp = 2 * Pfail * Pfail2 / (2 * self.pgs)
        exp += 2 * Pfail * 2 * Pnre * self.objsize / (self.size * self.full)
        self.test("3H", "Durability(rados,2cp)", v, exp, slop=0.01)

        # RADOS 2cp size
        v = rados2.rawsize
        exp = 2 * self.size
        self.test("3I", "RADOS 2cp raw size", v, exp)

        # RADOS 3cp P_drive vs bare disk
        rados3 = RADOS(e_disk, pg=self.pgs, speed=self.recovery,
                       nre_model="fail", fullness=self.full,
                       objsize=self.objsize, delay=0, stripe=1, copies=3)
        rados3.compute(period=YEAR)
        v = rados3.P_drive
        exp = 3 * Pfail * 2 * Pfail2 * Pfail2
        self.test("3J", "PFdrive(rados,3cp) = PFdrive(3 disks)", v, exp)

        # RADOS 3cp L_drive vs bare disk
        v = rados3.L_drive
        exp = self.size * self.full / (2 * self.pgs)
        self.test("3K", "Ldrive(rados,3cp) = size*full/2pg", v, exp)

        # RADOS nre=fail 3cp P_nre
        v = rados3.P_nre
        exp = 3 * Pfail * 2 * Pfail2 * 2 * Pnre
        self.test("3L", "Pnre(rados,3cp) vs disk", v, exp, slop=0.01)

        # RADOS nre=fail 3cp L_nre
        v = rados2.L_nre
        exp = self.size * self.full / self.pgs
        if exp > self.objsize:
            exp = self.objsize
        self.test("3M", "Lnre(rados,3cp) = min(pg/2,objsize)", v, exp)

        # RADOS 3cp durability
        v = 1.0 - rados3.dur    # complement for extra precision
        exp = 3 * Pfail * 2 * Pfail2 * Pfail2 / (2 * self.pgs)
        exp += 3 * Pfail * 2 * Pfail2 * 2 * Pnre * \
                self.objsize / (self.size * self.full)
        self.test("3N", "Durability(rados,3cp)", v, exp, slop=0.04)
        # FIX - why is this so far off ... examine the components

        # RADOS 3cp size
        v = rados3.rawsize
        exp = 3 * self.size
        self.test("3O", "RADOS 3cp raw size", v, exp)

        # RADOS nre=ignore, Lnre = 0
        rados3.nre_model = "ignore"
        rados3.compute(period=YEAR)
        v = rados3.L_nre
        exp = 0
        self.test("3P", "nre=ignore, Lnre=0", v, exp)

        # RADOS nre=ignore, Pnre = 0
        v = rados3.P_nre
        exp = 0
        self.test("3Q", "nre=ignore, Pnre=0", v, exp)

        # effects of recovery speed: half the speed, double P_fail
        rados2.speed /= 2
        rados2.compute(period=YEAR)
        v = rados2.P_drive
        rados2.speed *= 2
        exp = 2 * 2 * Pfail * Pfail2    # double the normal P_frail
        self.test("3R", "speed/2, Pfail*2", v, exp)

        # effects of period: double the period, double P_fail
        rados2.compute(period=2 * YEAR)
        v = rados2.P_drive
        exp = 2 * 2 * Pfail * Pfail2    # double the normal P_frail
        self.test("3S", "period*=2, Pfail*=2", v, exp, slop=0.01)

        # effects of mark-out: double time to recover, double P_fail
        rados2.delay = Tr
        rados2.compute(period=YEAR)
        v = rados2.P_drive
        rados2.delay = 0
        exp = 2 * 2 * Pfail * Pfail2    # double the normal P_fail
        self.test("3T", "markout=Tr, Pfail*=2", v, exp)

        # effects of striping: multiplies error probability
        rados2.stripe = self.stripe
        rados2.compute(period=YEAR)
        v = rados2.P_drive
        rados2.stripe = 1
        exp = self.stripe * 2 * Pfail * Pfail2    # pfail *= stripe factor
        self.test("3U", "stripe*n, Pfail*n", v, exp, slop=0.05)

        # efects of declustering: no effect on error probability
        rados2.pgs /= 2
        rados2.compute(period=YEAR)
        v = rados2.P_drive
        rados2.pgs *= 2
        exp = 2 * Pfail * Pfail2        # standard two copy
        self.test("3V", "pg/2, Pfail unchanged", v, exp)

        # efects of declustering: double the normal loss
        exp = self.size * self.full / self.pgs
        v = rados2.L_drive
        self.test("3W", "pg/2, loss*2", v, exp)

        # effects of fullness: half fullness, half the failures
        rados2.full /= 2
        rados2.compute(period=YEAR)
        rados2.full *= 2
        v = rados2.P_drive
        exp = (2 * Pfail * Pfail2) / 2
        self.test("3X", "full/2, Pfail/2", v, exp)

        # effects of fullness: half fullness, half the loss
        v = rados2.L_drive
        exp = self.size * self.full / (2 * 2 * self.pgs)
        self.test("3Y", "full/2, loss/2", v, exp)

    #
    # Site Reliability test suite
    #
    def siteTest(self):
        """ sanity check a site reliability simulation """

        # ball park estimates
        Pfail = float(self.s_fits) * YEAR / 1000000000
        mttf = 1000000000 / self.s_fits

        site = Site(fits=self.s_fits, size=self.s_size)

        # basic site FIT rates
        site.compute(period=YEAR)
        exp = Pfail
        v = site.P_site
        if self.test("4A", "1Y site fail rate", v, exp):
            Pfail = site.P_site     # move to more accurate value

        # single year durability
        v = 1.0 - site.dur      # complement for better precision
        exp = Pfail
        self.test("4B", "1Y Durability(site)", v, exp)

        # single year availability w/o repair
        exp = 1.0 - Pfail
        v = site.availability()
        self.test("4C", "1Y availability", v, exp)

        # double the period, double Pfail
        site.compute(period=2 * YEAR)
        exp = 2 * Pfail
        v = site.P_site
        self.test("4D", "2Y fail rate", v, exp)

        # two year durability
        v = 1.0 - site.dur      # complement for better precision
        exp = 2 * Pfail
        self.test("4E", "2Y Durability(site)", v, exp)

        # effects of multiples on P_fail
        site.compute(period=YEAR, mult=3)
        exp = Pfail * 3
        v = site.P_site
        self.test("4F", "3x 1Y fail rate", v, exp, slop=0.01)

        # site recovery rates and availability
        site.replace = mttf
        exp = 0.5       # mttr = mttf
        v = site.availability()
        self.test("4G", "long term availability", v, exp)

        # site raw size
        v = site.rawsize
        exp = self.s_size
        self.test("4Z", "per petabyte", v, exp)

    #
    # Multi-site RADOS Reliability test suite
    #
    def multiTest(self):
        """ sanity check a multi-site RADOS simulation """

        # the ballpark estimates get pretty complicated in this one

        # one disk failing during a year
        D_fail = float(self.fits) * YEAR / 1000000000
        # time for RADOS to recovery from one disk failure
        D_recover = float(self.full) * self.size / \
                            (self.recovery * self.pgs * 3600)
        # one disk experience and NRE during recovery
        D_nre = self.nre * self.full * self.size * 8
        # probability of losing a site
        S_fail = float(self.s_fits) * YEAR / 1000000000

        # time to recover a placement group from another site
        PG_size = self.size * self.full / (2 * self.pgs)
        PG_recover = float(self.full) * self.size / \
                            (self.s_recovery * self.pgs * 3600)
        # time to recover an object from another site
        O_recover = float(self.objsize) / (self.s_recovery * 3600)

        # instantiate the simulations
        e_disk = Disk(size=self.size, fits=self.fits, nre=self.nre,
                      desc="test")
        rados = RADOS(e_disk, pg=self.pgs, speed=self.recovery,
                      nre_model="fail", fullness=self.full,
                      objsize=self.objsize, delay=0, stripe=1, copies=2)
        site = Site(fits=self.s_fits, rplc=self.s_replace)
        multi = MultiSite(rados, site, speed=self.s_recovery,
                          latency=0, sites=1)

        # sanity check and calibration single site P(sitefail)
        multi.sites = 1
        multi.compute(period=YEAR)
        v = multi.P_site
        exp = S_fail
        if self.test("5A", "P(1 site failure)", v, exp):
            S_fail = multi.P_site

        # sanity check and calibration single site P(nre)
        v = multi.P_nre
        exp = 2 * D_fail * 2 * D_nre
        if self.test("5B", "Pnre(one site)", v, exp, slop=0.02):
            D_nre = multi.P_nre / (2 * 2 * D_fail)

        # single site L(sitefail)
        v = multi.L_site
        exp = site.size
        self.test("5C", "L(1 site failure)", v, exp)

        # ballpark probability of losing a site during site recovery
        S_fail2 = S_fail * self.s_replace / YEAR

        # two site P(sitefail)
        multi.sites = 2
        multi.compute(period=YEAR)
        v = multi.P_site
        exp = 2 * S_fail * S_fail2
        if self.test("5D", "P(2 site failure)", v, exp):
            S_fail2 = multi.P_site / (2 * S_fail)

        # two site L(sitefail)
        v = multi.L_site
        exp = site.size
        self.test("5E", "L(2 site failure)", v, exp)

        # three site P(sitefail)
        multi.sites = 3
        multi.compute(period=YEAR)
        v = multi.P_site
        exp = 3 * S_fail * 2 * S_fail2 * S_fail2
        self.test("5F", "P(3 site failure)", v, exp)

        # three site L(sitefail)
        v = multi.L_site
        exp = site.size
        self.test("5G", "L(3 site failure)", v, exp)

        # four site P(sitefail)
        multi.sites = 4
        multi.compute(period=YEAR)
        v = multi.P_site
        exp = 4 * S_fail * 3 * 2 * S_fail2 * S_fail2 * S_fail2
        self.test("5H", "P(4 site failure)", v, exp)

        # four site L(sitefail)
        v = multi.L_site
        exp = site.size
        self.test("5I", "L(4 site failure)", v, exp)

        # ballpark probability of losing both disks before recovering
        D_2fail = (2 * D_fail) * (self.pgs * (D_fail * D_recover / YEAR))

        # one site P(drivefail)
        multi.sites = 1
        multi.compute(period=YEAR)
        v = multi.P_drive
        exp = D_2fail
        if self.test("5J", "P(1 site drive failure)", v, exp, slop=0.01):
            D_2fail = multi.P_drive

        # single site durability includeing drive failure
        v = 1.0 - multi.dur     # complement for better precision
        exp = S_fail
        exp += D_2fail
        exp += 0                # Pnre is in the noise
        self.test("5K", "Durability(rados 1x2)", v, exp)

        # one site L(drivefail)
        v = multi.L_drive
        exp = PG_size
        self.test("5L", "L(1 site drive failure)", v, exp)

        # next site has a much shorter time in which to fail
        D_2more = 2 * ((D_fail * D_recover / YEAR) ** 2)

        # two site P(drivefail)
        multi.sites = 2
        multi.compute(period=YEAR)
        v = multi.P_drive
        exp = 0     # enumerating all the cases for clarity
        exp += (2 * D_2fail) * D_2more  # both sites lose all drives
        exp += (2 * S_fail) * D_2more   # lose one site, then all drives
        exp += (2 * D_2fail) * S_fail2  # lose all drives, then a site
        self.test("5M", "P(2 site drive failure)", v, exp)

        # dual site durability includeing drive failure
        v = 1.0 - multi.dur     # complement for better precision
        exp = 2 * S_fail * S_fail2
        exp += (2 * D_2fail) * D_2more  # both sites lose all drives
        exp += (2 * S_fail) * D_2more   # lose one site, then all drives
        exp += (2 * D_2fail) * S_fail2  # lose all drives, then a site
        exp += 0                        # Pnre is in the noise
        self.test("5N", "Durability(rados 2x2)", v, exp)

        # two site L(drivefail)
        v = multi.L_drive
        exp = PG_size
        self.test("5O", "L(2 site drive failure)", v, exp)

        # three site P(drivefail)
        multi.sites = 3
        multi.compute(period=YEAR)
        v = multi.P_drive
        exp = 0     # enumerating all the cases for clarity
        exp += (3 * D_2fail) * (2 * D_2more) * D_2more  # c, c, c
        exp += (3 * D_2fail) * (2 * D_2more) * S_fail2  # c, c, s
        exp += (3 * D_2fail) * (2 * S_fail2) * D_2more  # c, s, c
        exp += (3 * D_2fail) * (2 * S_fail2) * S_fail2  # c, s, s
        exp += (3 * S_fail) * (2 * D_2more) * D_2more   # s, c, c
        exp += (3 * S_fail) * (2 * D_2more) * S_fail2   # s, c, s
        exp += (3 * S_fail) * (2 * S_fail2) * D_2more   # s, s, c
        self.test("5P", "P(3 site drive failure)", v, exp)

        # tripple site durability including drive failure
        v = 1.0 - multi.dur     # complement for better precision
        exp = 3 * S_fail * 2 * S_fail2 * S_fail2
        exp += (3 * D_2fail) * (2 * D_2more) * D_2more  # c, c, c
        exp += (3 * D_2fail) * (2 * D_2more) * S_fail2  # c, c, s
        exp += (3 * D_2fail) * (2 * S_fail2) * D_2more  # c, s, c
        exp += (3 * D_2fail) * (2 * S_fail2) * S_fail2  # c, s, s
        exp += (3 * S_fail) * (2 * D_2more) * D_2more   # s, c, c
        exp += (3 * S_fail) * (2 * D_2more) * S_fail2   # s, c, s
        exp += (3 * S_fail) * (2 * S_fail2) * D_2more   # s, s, c
        exp += 0          # Pnre is in the noise
        self.test("5Q", "Durability(rados 3x2)", v, exp)

        # three site L(drivefail)
        v = multi.L_drive
        exp = PG_size
        self.test("5R", "L(3 site drive failure)", v, exp)

        # P(sitefail) vs site replacment time
        multi.sites = 2
        site.replace *= 2
        multi.compute(period=YEAR)
        site.replace /= 2
        v = multi.P_site
        exp = 2 * (2 * S_fail * S_fail2)
        self.test("5S", "2*replacement ->2*P(sitefail) ", v, exp)

        # P(rep)
        multi.latency = self.s_latency
        multi.compute(period=YEAR)
        exp = S_fail * multi.sites
        v = multi.P_rep
        self.test("5T", "PL(repfail)", v, exp)

        # L(rep) vs latency
        exp = self.s_latency * self.s_recovery / (2 * SECOND)
        v = multi.L_rep
        self.test("5U", "L(repfail) vs latency", v, exp)

        # L(rep) vs remote recovery rate
        multi.speed *= 2
        multi.compute(period=YEAR)
        multi.speed /= 2
        exp = 2 * self.s_latency * self.s_recovery / (2 * SECOND)
        v = multi.L_rep
        self.test("5V", "2*speed -> L(repfail)/2", v, exp)

        # NOTE: I tried to write a test around the remote recovery
        #       time but found it to be insignificant because of the
        #       rarity of remote drive recovery.

if __name__ == "__main__":
    test = Test()
    test.diskTest()
    test.raidTest()
    test.radosTest()
    test.siteTest()
    test.multiTest()

    if test.failed == 0:
        print "PASSED %d/%d tests" % (test.passed, test.passed)
    else:
        print "FAILED %d/%d tests" % (test.failed, test.passed + test.failed)
    if test.notyet > 0:
        print "(%d tests still unimplemented)" % test.notyet
