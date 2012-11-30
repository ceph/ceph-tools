#!/usr/bin/python
#
#
#

# size constant
GIG = 1000 * 1000 * 1000

import SimDisk
import disktest

print("\n7200 RPM DISK PERFORMANCE")
myDisk = SimDisk.SimDisk(rpm=7200)
disktest.disktest(myDisk, filesize=16 * GIG)

#print("\n20K IOP SSD PERFORMANCE")
#mySSD = SimDisk.SimSSD(size=2 * GIG, iops=20000)
#disktest.disktest(mySSD, filesize=16 * GIG)
