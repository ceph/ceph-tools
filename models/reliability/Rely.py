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

# basic disk reliability model
disk = DiskRely.Disk(size=disksize)

# annual probability of failure
p_fail = disk.p_failure(period=RelyFuncts.YEAR)
print("Annual probability of failure (per drive): %f" % (p_fail))
print("Non-recoverable read error rate: %6.2E" % (disk.nre))

hfmt = "%-16s  %12s %12s"
dfmt = "%-16s      %6.2E    %6.2E"

print()
print("Expected annual data loss (in bytes)")
print(hfmt % ("storage", "/drive", "/petabyte"))

# expected data loss due to single drive failures
loss_d = p_fail * disk.size             # per drive
loss_p = loss_d * disk.drives_per_pb    # per petabyte
print(dfmt % ("one copy", loss_d, loss_p))

# expected loss in RAID-5 groups due to multi-drive failure or NRE
raid5 = RaidRely.RAID5(disk)
p_fail = raid5.p_failure(period=RelyFuncts.YEAR, scrub=False)
loss_d = p_fail * disk.size             # per drive
loss_p = loss_d * disk.drives_per_pb    # per petabyte
print(dfmt % ("RAID-5 (noscrub)", loss_d, loss_p))

# expected loss in RAID-1 groups due to multi-drive failure or NRE
raid1 = RaidRely.RAID1(disk)
p_fail = raid1.p_failure(period=RelyFuncts.YEAR, scrub=False)
loss_d = p_fail * disk.size             # per drive
loss_p = loss_d * disk.drives_per_pb    # per petabyte
print(dfmt % ("RAID-1 (noscrub)", loss_d, loss_p))

# expected loss in RAID-5 groups due to multi-drive failures
p_fail = raid5.p_failure(period=RelyFuncts.YEAR, scrub=True)
loss_d = p_fail * disk.size             # per drive
loss_p = loss_d * disk.drives_per_pb    # per petabyte
print(dfmt % ("RAID-5 (w/scrub)", loss_d, loss_p))

# expected loss in RAID-1 groups due to multi-drive failures
p_fail = raid1.p_failure(period=RelyFuncts.YEAR, scrub=True)
loss_d = p_fail * disk.size             # per drive
loss_p = loss_d * disk.drives_per_pb    # per petabyte
print(dfmt % ("RAID-1 (w/scrub)", loss_d, loss_p))

# expected loss in RAID-6 groups due to multi-drive failures or NRE
raid6 = RaidRely.RAID6(disk)
p_fail = raid6.p_failure(period=RelyFuncts.YEAR, scrub=False)
loss_d = p_fail * disk.size             # per drive
loss_p = loss_d * disk.drives_per_pb    # per petabyte
print(dfmt % ("RAID-6 (noscrub)", loss_d, loss_p))

# expected loss in RAID-6 groups due to multi-drive failures
p_fail = raid6.p_failure(period=RelyFuncts.YEAR, scrub=True)
loss_d = p_fail * disk.size             # per drive
loss_p = loss_d * disk.drives_per_pb    # per petabyte
print(dfmt % ("RAID-6 (w/scrub)", loss_d, loss_p))

# expected loss in two-copy RADOS pools
rados2 = RadosRely.RADOS(disk, copies=2)
p_fail = rados2.p_failure(period=RelyFuncts.YEAR)
loss_d = p_fail * disk.size / rados2.pools
loss_p = loss_d * disk.drives_per_pb    # per petabyte
print(dfmt % ("RADOS (2 copy)", loss_d, loss_p))

# expected loss in three-copy RADOS pools
rados3 = RadosRely.RADOS(disk, copies=3)
p_fail = rados3.p_failure(period=RelyFuncts.YEAR)
loss_d = p_fail * disk.size / rados3.pools
loss_p = loss_d * disk.drives_per_pb    # per petabyte
print(dfmt % ("RADOS (3 copy)", loss_d, loss_p))
