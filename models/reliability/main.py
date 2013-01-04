#!/usr/bin/python
#
# exerciser for storage reliability models
#

import DiskRely
import RaidRely
import RadosRely

import TestRun

# instantiate a standard set of tests
disk = DiskRely.EnterpriseDisk()
raid1 = RaidRely.RAID1(disk)
raid5 = RaidRely.RAID5(disk)
raid6 = RaidRely.RAID6(disk)
rados2 = RadosRely.RADOS(disk)
rados3 = RadosRely.RADOS(disk, copies=3)
TestRun.TestRun((disk, raid5, raid1, rados2, raid6, rados3))
