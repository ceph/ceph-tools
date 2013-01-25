#!/usr/bin/python
#
#   this is a configuration file for a performance simulation
#

# size constants
MEG = 1000 * 1000
GIG = 1000 * MEG
TERA = 1000 * GIG

import test

data = {        # data storage devices
    'fs': "xfs"
}

journal = {     # journal devices
    'device': "ssd",
    'size': 1 * GIG,
    'speed': 400 * MEG,
    'iops': 30000,
    'streams': 8,
    'fs': "xfs",
    'shared': True
}

cluster = {     # cluster configuration
    'front': 10 * GIG,
    'back': 10 * GIG,
    'nodes': 3,
    'osd_per_node': 6
}

tests = {       # what tests to run with what parameters
    # raw disk parameters and simulations
    'DiskParms': False,
    'FioJournal': True,
    'FioRdepths': [1, 32],
    'FioRsize': 16 * GIG,

    # FIO performance tests
    'FioFdepths': [1, 32],
    'FioFsize': 16 * GIG,

    # filestore performance tests
    'SioFdepths': [16],
    'SioFsize': 1 * GIG,
    'SioFnobj': 2500,

    # RADOS performance tests
    'SioRdepths': [16],
    'SioRsize': 1 * GIG,
    'SioRnobj': 2500 * 3 * 6,   # multiply by number of OSDs
    'SioRcopies': [2],
    'SioRclients': [3],
    'SioRinstances': [4]
}

test.test(data, journal, cluster, tests)
