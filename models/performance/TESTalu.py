#!/usr/bin/python
#
#   this is a configuration file for a performance simulation
#   that captures (I believe) the parameters to simulate the
#   ALU results
#

from units import *
import test

data = {        # data storage devices
    'device': "disk",
    'fs': "xfs"
}

journal = {     # journal devices
    'device': "ssd",
    'size': 1 * GIG,
    'speed': 110 * MEG,
    'iops': 30000,
    'streams': 8,
    'fs': "xfs",
    'shared': True
}

cluster = {     # cluster configuration
    'front': 10 * GIG,
    'back': 10 * GIG,
    'nodes': 22,
    'osd_per_node': 2
}

tests = {       # what tests to run with what parameters
    # raw disk parameters and simulations
    'DiskParms': False,
    'FioJournal': False,
    'FioRdepths': [],
    'FioRsize': 16 * GIG,

    # FIO performance tests
    'FioFdepths': [1, 32],
    'FioFsize': 16 * GIG,

    # filestore performance tests
    'SioFdepths': [16],
    'SioFsize': 4 * MEG,
    'SioFnobj': 2500,

    # RADOS performance tests
    'SioRdepths': [16],
    'SioRsize': 1 * MEG,
    'SioRnobj': 2500,
    'SioRcopies': [2],
    'SioRclients': [3],
    'SioRinstances': [4]
}

test.test(data, journal, cluster, tests)
