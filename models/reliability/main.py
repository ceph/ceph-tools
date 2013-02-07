#!/usr/bin/python
#
# exerciser for storage reliability models
#

import DiskRely
import RaidRely
import RadosRely
import SiteRely
import MultiSite


import TestRun

# instantiate a standard set of tests
disk = DiskRely.EnterpriseDisk()

raid1 = RaidRely.RAID1(disk)
raid5 = RaidRely.RAID5(disk)
raid6 = RaidRely.RAID6(disk)

rados1 = RadosRely.RADOS(disk, copies=1)
rados2 = RadosRely.RADOS(disk, copies=2)
rados3 = RadosRely.RADOS(disk, copies=3)

site = SiteRely.Site()

multi11 = MultiSite.MultiSite(rados1, site, sites=1)
multi21 = MultiSite.MultiSite(rados1, site, sites=2)
multi31 = MultiSite.MultiSite(rados1, site, sites=3)
multi41 = MultiSite.MultiSite(rados1, site, sites=4)
multi12 = MultiSite.MultiSite(rados2, site, sites=1)
multi22 = MultiSite.MultiSite(rados2, site, sites=2)
multi32 = MultiSite.MultiSite(rados2, site, sites=3)
multi42 = MultiSite.MultiSite(rados2, site, sites=4)

TestRun.TestRun((disk, raid5, raid1, rados2, raid6, rados3,
    site, multi11, multi21, multi31, multi41,
    multi12, multi22, multi32, multi42))
