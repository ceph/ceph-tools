#!/usr/bin/python
#
# Ceph - scalable distributed file system
#
# Copyright (C) Inktank
#
# This is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 2.1, as published by the Free Software
# Foundation.  See file COPYING.
#

"""
Default values and the object that contains them
(e.g. passed into and back from the GUI)
"""
from RelyFuncts import SECOND, MINUTE, HOUR, DAY, YEAR, FitRate

# speeds and disk sizes
MiB = 1000000
GiB = MiB * 1000
TiB = GiB * 1000

# file sizes
KB = 1024
MB = KB * 1024
GB = MB * 1024
TB = GB * 1024


class Config:

    def __init__(self):
        """ default test parameters """

        self.period = 1.0 * YEAR
        self.verbose = "all"

        self.disk_type = "Enterprise"
        self.disk_size = 2 * TiB
        self.disk_nre = 1E-16
        self.disk_fit = 826
        self.disk_fit2 = 826
        self.nre_model = "fail"

        self.node_fit = 1000

        self.raid_vols = 2
        self.raid_replace = 6.0 * HOUR
        self.raid_recover = 20 * MiB

        self.rados_copies = 2
        self.rados_markout = 10.0 * MINUTE
        self.rados_recover = 50 * MiB
        self.rados_osds = 2
        self.rados_decluster = 200
        self.rados_fullness = 0.75

        self.obj_size = 1 * GB
        self.stripe_length = 1

        self.remote_sites = 1
        self.remote_recover = 10 * MiB
        self.remote_latency = 0.0 * SECOND
        self.majeure = FitRate(.001, YEAR)
        self.site_recover = 30.0 * DAY
