#!/usr/bin/python
#
# note that by this point, all times are in hours
#

# speeds and disk sizes
M = 1000000
G = M * 1000
T = G * 1000

# file sizes
KB = 1024
MB = KB * 1024
GB = MB * 1024
TB = GB * 1024

import RelyFuncts


class TestConfig:

    def __init__(self):
        """ default test parameters """

        self.period = 365.25 * 24
        self.parms = 1
        self.headings = 1

        self.disk_type = "Enterprise"
        self.disk_size = 2 * T
        self.disk_nre = 1E-15
        self.disk_fit = 826
        self.nre_meaning = "fail+error"

        self.node_fit = 1000

        self.raid_vols = 2
        self.raid_replace = 6
        self.raid_recover = 50 * M

        self.rados_copies = 2
        self.rados_markout = 10.0 / 60
        self.rados_recover = 50 * M
        self.rados_decluster = 200
        self.rados_fullness = 0.75

        self.obj_size = 1 * GB
        self.stripe_width = 4 * MB

        self.remote_sites = 1
        self.remote_recover = 10 * M
        self.remote_latency = 0
        self.remote_replace = 6 * 30 * 24
        self.majeure = RelyFuncts.BILLION / (1000 * RelyFuncts.YEAR)
        self.site_recover = 0
