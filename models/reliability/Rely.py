#!/usr/bin/python
#
# basic reliability models
#


import RelyFuncts
import DiskRely
import RaidRely
import RadosRely

KB = 1000
MB = KB * 1000
GB = MB * 1000
TB = GB * 1000
PB = TB * 1000

# basic modeling parameters
disksize = 2 * TB
recovery = 50 * MB
T_replace = float(RelyFuncts.HOUR) * 6
T_markout = float(RelyFuncts.HOUR) * 10 / 60

# instantiate the models
disk = DiskRely.EnterpriseDisk(size=disksize)
raid1 = RaidRely.RAID1(disk, recovery=recovery, delay=T_replace)
raid5 = RaidRely.RAID5(disk, recovery=recovery, delay=T_replace)
raid6 = RaidRely.RAID6(disk, recovery=recovery, delay=T_replace)
rados2 = RadosRely.RADOS(disk, copies=2, speed=recovery, delay=T_markout)
rados3 = RadosRely.RADOS(disk, copies=3, speed=recovery, delay=T_markout)

print("Disk Modeling Parameters (%s)" % (disk.description))
print("    size:      %dGB" % (disk.size / GB))
print("    FIT rate:  %d (%f/year)" % \
      (disk.fits, disk.p_failure(period=RelyFuncts.YEAR)))
print("    NRE rate:  %6.2E" % (disk.nre))
print()
print("  Recovery Speeds (and assumptions):")
print("    RAID-1:     %3d MB/s (replace in %d hours)" % \
          (raid1.speed / MB, T_replace))
print("    RAID-5:     %3d MB/s (replace in %d hours)" % \
        (raid5.speed / MB, T_replace))
print("    RAID-6:     %3d MB/s (replace in %d hours)" % \
        (raid6.speed / MB, T_replace))
print("    RADOS:      %3d MB/s (fully declustered, markout=%d min)" % \
        (rados2.speed / MB, T_markout * 60))

hfmt = "    %-20s %12s %12s %12s"
dfmt = "    %-20s %11.6f%% %12.2E %12.2E"
print()
print("Expected annual data loss (per drive, per petabyte)")
print(hfmt % ("storage", "prob/drive", "bytes/drive", "bytes/peta"))
print(hfmt % ("--------", "--------", "--------", "--------"))

# expected data loss due to single drive failures
for d in (disk, raid5, raid1, rados2, raid6, rados3):
    p_fail = d.p_failure(period=RelyFuncts.YEAR)
    loss_d = p_fail * d.loss()
    loss_p = loss_d * PB / disk.size
    print(dfmt % (d.description, p_fail*100, loss_d, loss_p))
