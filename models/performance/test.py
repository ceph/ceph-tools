#!/usr/bin/python
#
#   this is the script that creates the objects to be
#   tested and kicks off the high level tests
#

# size constants
MEG = 1000 * 1000
GIG = 1000 * 1000 * 1000

import SimDisk
import SimFS
import disktest
import fstest
import FileStore
import filestoretest

myDisk = SimDisk.Disk(rpm=7200)
myDumb = SimDisk.DumbDisk(rpm=7200)
mySsd = SimDisk.SSD(1 * GIG, iops=4000, streams=8)

print("\n")
print("%d RPM Smart Drive Characteristics" % myDisk.rpm)
disktest.disktest(myDisk, filesize=16 * GIG)

for d in (1, 32):
    print("\n")
    print("%d RPM Smart Drive, depth=%d" % (myDisk.rpm, d))
    disktest.tptest(myDisk, filesize=16 * GIG, depth=d)

print("\n")
print("%d RPM Dumb Drive" % myDumb.rpm)
disktest.tptest(myDumb, filesize=16 * GIG, depth=1)

for d in (1, 32):
    print("\n")
    print("%d IOP, %dMB/s SSD, depth=%d" %
        (mySsd.max_iops, mySsd.media_speed / MEG, d))
    disktest.tptest(mySsd, filesize=16 * GIG, depth=d)

myFS = SimFS.btrfs(myDisk)
for d in (1, 32):
    print("\n")
    print("FIO (direct) to local file system, depth=%d" % (d))
    fstest.fstest(myFS, filesize=16 * GIG, depth=d)

#d = 1
#print("\n")
#print("FIO (sync) to local file system, depth=%d" % (d))
#fstest.fstest(myFS, filesize=16 * GIG, depth=d, sync=True)

print("\n")
myFstore_l = FileStore.FileStore(myFS, None)
myJrn = SimFS.btrfs(mySsd)
myFstore_s = FileStore.FileStore(myFS, myJrn)

print("Journal on the data file system")
for d in (1, 32):
    print("\n")
    print("smalliobench-fs, depth=%d" % (d))
    filestoretest.fstoretest(myFstore_l, obj_size=16 * GIG, depth=d)

print()
print("Journal on SSD")
for d in (1, 32):
    print("\n")
    print("smalliobench-fs, depth=%d" % (d))
    filestoretest.fstoretest(myFstore_s, obj_size=16 * GIG, depth=d)
