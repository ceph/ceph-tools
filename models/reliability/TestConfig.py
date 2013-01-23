#!/usr/bin/python
#
# note that by this point, all times are in hours
#

MB = 1000000
GB = MB * 1000
TB = GB * 1000


class TestConfig:

    def __init__(self):
        """ default test parameters """

        self.period = 365.25 * 24
        self.nre_meaning = "ignore"
        self.obj_size = 1 * GB

        self.disk_size = 2 * TB
        self.disk_nre = 1E-15
        self.disk_fit = 826

        self.raid_vols = 2
        self.raid_replace = 6
        self.raid_recover = 50 * MB

        self.rados_copies = 2
        self.rados_markout = 10.0 / 60
        self.rados_recover = 50 * MB
        self.rados_decluster = 200

        self.remote_sites = 1
        self.remote_recover = 10 * MB
        self.remote_replace = 6 * 30 * 24
        self.majeure = 0
