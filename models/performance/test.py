#!/usr/bin/python
#
# Ceph - scalable distributed file system
#
# NO COPYRIGHT/COPYLEFT
#
#   This module merely invokes a simulation and displays
#   the results using standard reporting functions.  As it
#   merely uses those API's it is an "application" under the
#   Gnu Lesser General Public Licence.  It can be reproduced,
#   modified, and distributed without restriction.
#
from units import *


#
# configuration for components to be simulated
#
data = {
    'device': "disk",
    'fs': "xfs"
}

journal = {
    'device': "ssd",
    'size': 1 * GIG,
    'speed': 400 * MEG,
    'iops': 30000,
    'streams': 8,
    'fs': "xfs",
    'shared': True      # FIX obsolete ???
}

storage_node = {
    'cpu': "xeon",
    'speed': 2.2 * GIG,
    'cores': 2,
    'cpus': 1,
    'ram': 64 * GIG,
    'osd_per_journal': 4,
}

cluster = {
    'front': 1 * GIG,
    'back': 10 * GIG,
    'nodes': 4,
    'osd_per_node': 4,
}

#
# tests to be run
#
tests = {
    # raw disk parameters and simulations
    'DiskParms': True,
    'FioRdepth': [1, 32],
    'FioRsize': 16 * GIG,
    'FioRbs': (4096, 128 * 1024, 4096 * 1024),

    # FIO performance tests
    'FioJournal': True,
    'FioFdepth': [1, 32],
    'FioFsize': 16 * GIG,
    'FioFbs': (4096, 128 * 1024, 4096 * 1024),
    'Fmisc': False,

    # filestore performance tests
    'SioFdepth': [16],
    'SioFsize': 1 * GIG,
    'SioFnobj': 2500,
    'SioFbs': (4096, 128 * 1024, 4096 * 1024),

    # RADOS performance tests
    'SioRdepth': [16],
    'SioRsize': 1 * GIG,
    'SioRnobj': 2500 * 4 * 4,   # multiply by number of OSDs
    'SioRcopies': [2],
    'SioRclient': [3],
    'SioRinst': [4],
    'SioRbs': (4096, 128 * 1024, 4096 * 1024),
}

#
# main routine
#   instantiate the described objects and run the described tests
#
if __name__ == '__main__':

    from optparse import OptionParser
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("-d", "--data", dest="sim", action="store_true",
                      default=False,
                      help="produce simulated FS performance data")
    (opts, files) = parser.parse_args()

    # instantiate the journal device
    import SimDisk
    if journal is not None:
        myJDisk = SimDisk.makedisk(journal)
        if 'DiskParms' in tests and tests['DiskParms']:
            print("Journal Device Characteristics")
            SimDisk.diskparms(myJDisk)

    # instantiate the data device
    myDDisk = SimDisk.makedisk(data)
    if 'DiskParms' in tests and tests['DiskParms']:
        print("Data Device Characteristics")
        SimDisk.diskparms(myDDisk)

    # fio to the raw devices (journal and data)
    if journal is not None:
        SimDisk.tptest(myJDisk, tests, descr="Raw journal device")
    SimDisk.tptest(myDDisk, tests, descr="Raw data device")

    # instantiate and test the journal file system
    import SimFS
    if journal is not None:
        myJrnl = SimFS.makefs(myJDisk, journal)
        jrnl_desc = "journal FS (%s on %s)" % (myJrnl.desc, myJDisk.desc)
        SimFS.fstest(myJrnl, tests, descr=jrnl_desc)
    else:
        myJrnl = None
        jrnl_desc = "journal on data disk"

    # instantiate and test the data file system
    myData = SimFS.makefs(myDDisk, data)
    data_desc = "data FS (%s on %s)" % (myData.desc, myDDisk.desc)
    SimFS.fstest(myData, tests, descr=data_desc)

    # instantiate and test the filestore with the journal
    import FileStore
    myFstore = FileStore.makefilestore(myData, myJrnl, storage_node)
    if journal is not None:
        if 'osd_per_journal' in storage_node:
            if storage_node['osd_per_journal'] > 1:
                jrnl_desc += "/%d" % storage_node['osd_per_journal']
        msg = "%s, %s" % (data_desc, jrnl_desc)
        FileStore.filestoretest(myFstore, tests, descr=msg)
        nojFstore = FileStore.makefilestore(myData, None, storage_node)
    else:
        nojFstore = myFstore
        msg = "%s, %s" % (data_desc, "journal on data disk")

    # retest test the file store without a journal
    msgn = "%s, %s" % (data_desc, "journal on data disk")
    FileStore.filestoretest(nojFstore, tests, descr=msgn)

    # instantiate the RADOS simulation
    import Rados
    myRados = Rados.makerados(myFstore, cluster)
    Rados.radostest(myRados, tests, descr=msg)

    # check for warnings
    if myFstore.warnings != "" or myRados.warnings != "":
        print("WARNINGS: %s%s" % (myFstore.warnings, myRados.warnings))

#    if opts.sim:
#        test(data, journal, cluster, notests)
#    else:
#        test(data, journal, cluster, tests)
#    # just generate simulation data
#    notests = {
#        'FioFsize': 16 * GIG,
#        'perfdata': True
#    }
#
#def sample(name, fs, sz):
#    """ collect performance sample data for simulated file system
#        name -- name of the sample
#        fs -- file system to be sampled
#        sz -- fio file size to be simulated
#    """
#    sizes = {
#        '4k': 4086,
#        '128k': 128 * 1024,
#        '4m': 4 * 1024 * 1024
#    }
#
#    print("%sData = {" % (name))
#    print("    'source': 'sampled %s on %s'," % (fs.desc, fs.disk.desc))
#    for d in (1, 32):
#        for b in ("4k", "128k", "4m"):
#            bs = sizes[b]
#            tsr = fs.read(bs, sz, seq=True, depth=d, direct=True)
#            print("    'seq-read-%s-d%d': %d," % (b, d, MEG * bs / tsr))
#            tsw = fs.write(bs, sz, seq=True, depth=d, direct=True)
#            print("    'seq-write-%s-d%d': %d," % (b, d, MEG * bs / tsw))
#            trr = fs.read(bs, sz, seq=False, depth=d, direct=True)
#            print("    'rand-read-%s-d%d': %d," % (b, d, MEG * bs / trr))
#            trw = fs.write(bs, sz, seq=False, depth=d, direct=True)
#            print("    'rand-write-%s-d%d': %d," % (b, d, MEG * bs / trw))
#    print("    }")
#
#    # and capture sampled performance just in case anyone cares
#    if 'perfdata' in tests:
#        print("#")
#        print("# Sampled file system throughput to be fed into DataFS.py to")
#        print("# enable filestore simulation based on actual FS performance")
#        print("#")
#        print("")
#        sample("Data", myData, sz)
#        if myJrnl is not None:
#            print("")
#            sample("Jrnl", myJrnl, sz)
