#!/usr/bin/python
#
#   this script creates the objects to be tested and kicks off
#   a standard set of tests
#

# size constants
MEG = 1000 * 1000
GIG = 1000 * 1000 * 1000

# simulation classes
import SimDisk
import SimFS
import FileStore
import Rados

# test classes
import disktest
import fstest
import filestoretest
import radostest

#
# which tests to run for which parameter values
#
DiskParms = True
DiskDepths = [1, 32]
FioDepths = [1, 32]
SioFdepths = [16]
SioRdepths = [16]
SioRcopies = [2]
SioRclients = [3]
SioRinstances = [4]

# create standard disk simulations
myDisk = SimDisk.Disk(rpm=7200)
myDumb = SimDisk.DumbDisk(rpm=7200)
mySsd = SimDisk.SSD(1 * GIG, bw=400 * MEG, iops=30000, streams=8)

# create standard file system simulations
myXFS = SimFS.xfs(myDisk)
myBTR = SimFS.btrfs(myDisk)
myEXT4 = SimFS.ext4(myDisk)

#
# these are the assignments that define the cluster to be simulated
#
front = 10 * GIG            # front side NIC speed
back = 10 * GIG             # back side NIC speed
nodes = 4                   # storage nodes in cluster
osd_per = 4                 # OSDs per storage node
myFS = myXFS                # OSD file systems
myJrn = SimFS.xfs(mySsd)    # journal file system
myFstore = FileStore.FileStore(myFS, myJrn, journal_share=osd_per)
myRados = Rados.Rados(myFstore,
            front_nic=front, back_nic=back,
            nodes=nodes, osd_per_node=osd_per)

# file sizes and object counts to use for tests
sizeFIO = 16 * GIG
sizeSioF = 1 * GIG
sizeSioR = 1 * GIG
nobjSioF = 2500
nobjSioR = nodes * osd_per * nobjSioF

# introspect descriptions of the data and journal file systems
data_fs = myFS.__class__.__name__
data_dev = myFS.disk.__class__.__name__
data_desc = "data FS (%s on %s)" % (data_fs, data_dev)
jrnl_share = ""
if myJrn is not None:
    jrnl_fs = myJrn.__class__.__name__
    jrnl_dev = myJrn.disk.__class__.__name__
    jrnl_desc = "journal FS (%s on %s)" % (jrnl_fs, jrnl_dev)
    if osd_per > 1:
        jrnl_share = "/%d" % (osd_per)
else:
    jrnl_desc = "journal on data disk"

#
# run the specified tests for the specified values
#
if DiskParms:
    if myJrn is not None:
        print("Journal Device Characteristics")
        disktest.disktest(myJrn.disk, filesize=16 * GIG)
        print("")
    print("Data Device Characteristics")
    disktest.disktest(myDisk, filesize=sizeFIO)
    print("")

for d in DiskDepths:
    print("Raw disk, depth=%d" % (d))
    disktest.tptest(myDisk, filesize=sizeFIO, depth=d)
    print("")

if myJrn is not None:
    for d in FioDepths:
        print("FIO (direct) to %s, depth=%d" % (jrnl_desc, d))
        fstest.fstest(myJrn, filesize=sizeFIO, depth=d, direct=True)
        print("")

for d in FioDepths:
    print("FIO (direct) to %s, depth=%d" % (data_desc, d))
    fstest.fstest(myFS, filesize=sizeFIO, depth=d, direct=True)
    print("")

msg = "smalliobench-fs, %s, %s%s, depth=%d"
for d in SioFdepths:
    print(msg % (data_desc, jrnl_desc, jrnl_share, d))
    print("\tnobj=%d, objsize=%d" % (nobjSioF, sizeSioF))
    filestoretest.fstoretest(myFstore, nobj=nobjSioF,
                            obj_size=sizeSioF, depth=d)
    print("")

msg = "smalliobench-rados (%dx%d), %d copy, clients*instances*depth=(%d*%d*%d)"
for x in SioRcopies:
    for c in SioRclients:
        for i in SioRinstances:
            for d in SioRdepths:
                print(msg % (nodes, osd_per, x, c, i, d))
                print("\t%s, %s%s, nobj=%d, objsize=%d" %
                        (data_desc, jrnl_desc, jrnl_share, nobjSioR, sizeSioR))
                radostest.radostest(myRados, obj_size=sizeSioR, nobj=nobjSioR,
                                    clients=c, depth=i * d, copies=x)
                print("")

# check for warnings
if myFstore.warnings != "" or myRados.warnings != "":
    print("WARNINGS: %s%s" % (myFstore.warnings, myRados.warnings))
