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
RAID reliability model
    the modeled unit is a RAID set
"""

from RelyFuncts import SECOND, HOUR, YEAR

DELAY = 6 * HOUR                # pretty fast replacement
RECOVER = 50000000              # per disk in from set
MODEL = "fail+error"            # fail on detected NRE
                                # undetected errors get through
OBJSIZE = 1000000000            # default object size


class RAID(object):
    """ model a mirrored raid set """

    def __init__(self, disk, volumes, recovery, delay, nre_model, objsize):
        """ create a RAID reliability simulation
            disk -- underlying disk
            volumes -- number of total volumes in set
            recovery -- rebuild rate (bytes/second)
            delay -- rebuild delay (hours)
            nre_model -- how to handle NREs
            objsize -- average object size for NRE damage
        """
        self.disk = disk
        self.speed = recovery
        self.volumes = volumes
        self.delay = delay
        self.nre_model = nre_model
        self.objsize = objsize
        self.parity = 0
        self.copies = 1
        self.size = disk.size
        self.rawsize = disk.size * volumes  # size of a RAID set

        self.P_rep = 0      # inapplicable
        self.L_rep = 0      # inapplicable
        self.P_site = 0     # inapplicable
        self.L_site = 0     # inapplicable

    def rebuild_time(self):
        seconds = self.disk.size / self.speed
        return seconds * SECOND

    def compute(self, period=YEAR):
        """ probability of an arbitrary object surviving the period """

        # probability of an initial failure of any volume in the set
        self.disk.compute(period=period, mult=self.volumes)

        # how many disks do we need to do the recovery
        survivors = self.volumes - 1
        if self.parity > 0:
            required = self.volumes - self.parity
        elif self.copies > 1:
            required = 1
        else:
            required = self.volumes

        # can we recover from the loss of a single drive
        if survivors >= required:
            # probability of losing all but the last drive
            p = self.disk.P_drive
            recover = float(self.delay) + self.rebuild_time()
            while survivors > required:
                self.disk.compute(period=recover, mult=survivors,
                                  secondary=True)
                p *= self.disk.P_drive
                survivors -= 1

            # probability of losing the last drive
            self.disk.compute(period=recover, mult=survivors,
                              secondary=True)
            self.P_drive = p * self.disk.P_drive
            self.L_drive = self.size

            # probability of NRE on the last drive
            read_bytes = self.disk.size * required
            write_bytes = self.disk.size
            self.P_nre = p * self.disk.p_nre(bytes=read_bytes + write_bytes)
        else:   # we couldn't withstand even a single failure
            self.P_drive = self.disk.P_drive
            self.L_drive = self.disk.L_drive
            self.P_nre = self.disk.P_nre    # semi-arbitrary

        # compute the expected loss due to NRE
        self.L_nre = self.size
        self.dur = 1.0 - (self.P_drive + self.P_nre)
        if self.nre_model == "ignore":
            self.P_nre = 0
            self.L_nre = 0
        if self.nre_model == "error":
            self.L_nre = self.objsize
        elif self.nre_model == "error+fail/2":
            self.L_nre = (self.size + self.objsize) / 2

        self.dur = 1.0 - (self.P_drive + self.P_nre)


class RAID0(RAID):
    """ model a striped RAID set """

    def __init__(self, disk, volumes=2,   # default 2 stripes
                 recovery=0,              # efficient recovery
                 delay=0,                 # moderatly responsive
                 nre_model=MODEL,         # optimum durability
                 objsize=OBJSIZE):

        RAID.__init__(self, disk, volumes=volumes, recovery=recovery,
                      delay=delay, nre_model=nre_model, objsize=objsize)
        self.parity = 0
        self.size = disk.size * volumes
        self.description = "RAID-0: %d vol" % (volumes)


class RAID1(RAID):
    """ model a mirrored RAID set """

    def __init__(self, disk, volumes=2,   # default 2 mirror
                 recovery=RECOVER,        # efficient recovery
                 delay=DELAY,             # moderatly responsive
                 nre_model=MODEL,         # optimum durability
                 objsize=OBJSIZE):

        RAID.__init__(self, disk, volumes=volumes, recovery=recovery,
                      delay=delay, nre_model=nre_model, objsize=objsize)
        self.parity = 0
        self.copies = volumes
        self.description = "RAID-1: %d cp" % (volumes)


class RAID5(RAID):
    """ model a RAID set with one parity volume """

    def __init__(self, disk, volumes=4,  # default 3+1
                 recovery=RECOVER / 3,   # recovery from three volumes
                 delay=DELAY,            # moderatly responsive
                 nre_model=MODEL,        # optimum durability
                 objsize=OBJSIZE):

        RAID.__init__(self, disk, volumes=volumes, recovery=recovery,
                      delay=delay, nre_model=nre_model, objsize=objsize)
        self.parity = 1
        self.size = disk.size * (volumes - 1)
        self.description = "RAID-5: %d+%d" % (volumes - 1, 1)


class RAID6(RAID):
    """ model a RAID set with two parity volumes """

    def __init__(self, disk, volumes=8,  # default 6+2
                 recovery=RECOVER / 6,   # recovery from six volumes
                 delay=DELAY,            # moderatly responsive
                 nre_model=MODEL,        # optimum durability
                 objsize=OBJSIZE):

        RAID.__init__(self, disk, volumes=volumes, recovery=recovery,
                      delay=delay, nre_model=nre_model, objsize=objsize)
        self.parity = 2
        self.size = disk.size * (volumes - 2)
        self.description = "RAID-6: %d+%d" % (volumes - 2, 2)
