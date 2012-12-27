#!/usr/bin/python
#
#   this is the script that creates the objects to be
#   tested and kicks off the high level tests
#

# size constants
MEG = 1000 * 1000
GIG = 1000 * 1000 * 1000

import SimDisk      # disk simulations
myDisk = SimDisk.Disk(rpm=7200)
myDumb = SimDisk.DumbDisk(rpm=7200)
mySsd = SimDisk.SSD(1 * GIG, iops=4000, streams=8)

import SimFS        # file system simulations
myFS = SimFS.btrfs(myDisk)
myJrn = SimFS.btrfs(mySsd)

import FileStore    # filestore simulations
myFstore_l = FileStore.FileStore(myFS, None)
myFstore_s = FileStore.FileStore(myFS, myJrn)

import Rados        # RADOS simulations
nodes = 4
osd_per = 2
myRados_l = Rados.Rados(myFstore_l, nodes=nodes, osd_per_node=osd_per)
myRados_s = Rados.Rados(myFstore_s, nodes=nodes, osd_per_node=osd_per)

# disk simulation exerciser
import disktest

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


# file system simulation exerciser
import fstest
for d in (1, 32):
    print("\n")
    print("FIO (direct) to local file system, depth=%d" % (d))
    fstest.fstest(myFS, filesize=16 * GIG, depth=d)

#d = 1
#print("\n")
#print("FIO (sync) to local file system, depth=%d" % (d))
#fstest.fstest(myFS, filesize=16 * GIG, depth=d, sync=True)

print("\n")

# filestore simulation exerciser
import filestoretest
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

nodes = 4
osd_per = 2

# RADOS simulation exerciser
import radostest
copies = 2
print()
for d in (1, 32, 128):
    print("\n")
    print("smalliobench-rados (%dx%d), journal to disk, depth=%d, copies=%d" \
        % (nodes, osd_per, d, copies))
    radostest.radostest(myRados_l, obj_size=16 * GIG, depth=d)

print()
for d in (1, 32, 128):
    print("\n")
    print("smalliobench-rados (%dx%d), journal to ssd, depth=%d, copies=%d" \
        % (nodes, osd_per, d, copies))
    radostest.radostest(myRados_s, obj_size=16 * GIG, depth=d)
