#
# RAID reliability models
#

import RelyFuncts

DELAY = 6 * RelyFuncts.HOUR     # pretty fast replacement
RECOVER = 50000000              # per disk in from set
NRE = "fail+error"              # fail on detected NRE
                                # undetected errors get through


class RAID:
    """ model a mirrored raid set """

    def __init__(self, disk, volumes, recovery, delay, nre):
        """ create a RAID reliability simulation
            disk -- underlying disk
            volumes -- number of total volumes in set
            recovery -- rebuild rate (bytes/second)
            delay -- rebuild delay (hours)
            nre -- how to handle NREs
        """
        self.disk = disk
        self.speed = recovery
        self.volumes = volumes
        self.delay = delay
        self.nre = nre
        self.parity = 0

    def rebuild_time(self):
        seconds = self.disk.size / self.speed
        return seconds * RelyFuncts.SECOND

    def p_failure(self, period=RelyFuncts.YEAR):
        """ probability of data loss during a period """

        # probability of an initial disk failure
        p_fail = self.disk.p_failure(period=period)

        # probability of another failure during re-silvering
        recover = float(self.delay) + self.rebuild_time()
        p_fail2 = self.disk.p_failure(period=recover)

        # probability of losing the remaining redundancy
        survivors = self.parity if self.parity > 0 else self.volumes - 1
        from_set = 1 if self.parity == 0 else self.volumes - self.parity
        while survivors > 0 and from_set > 0:
            p_fail *= (p_fail2 * from_set)
            survivors -= 1
            if self.parity > 0:
                from_set -= 1

        return p_fail

    def loss(self):
        """ amount of data lost after a drive failure during recovery """
        return self.disk.size

    def p_nre(self):
        """ probability of an NRE during recovery """
        if self.nre == "ignore":
            return 0
        else:
            from_set = 1 if self.parity == 0 else self.volumes - self.parity
            # FIX ... this only works for disk size * nre << 1
            return from_set * self.disk.size * self.disk.nre

    def loss_nre(self, objsize=0):
        """ amount of data lost by NRE during recovery """
        if self.nre == "ignore":
            return 0
        elif self.nre == "fail":
            return self.disk.size

        badBytes = self.disk.corrupted_bytes(self.disk.size)
        if self.nre == "error":
            return badBytes     # one NRE = one lost byte
        else:   # half lost objects, half undetected errors
            return (badBytes + self.disk.size) / 2


class RAID1(RAID):
    """ model a mirrored RAID set """

    def __init__(self, disk, volumes=2,   # default 2 mirror
            recovery=RECOVER,             # efficient recovery
            delay=DELAY,                  # moderatly responsive
            nre=NRE):                     # optimum durability

        RAID.__init__(self, disk, volumes=volumes, recovery=recovery,
                      delay=delay, nre=nre)
        self.parity = 0
        self.description = "RAID-1: %d cp" % (volumes)


class RAID5(RAID):
    """ model a RAID set with one parity volume """

    def __init__(self, disk, volumes=4,  # default 3+1
            recovery=RECOVER / 3,        # recovery from three volumes
            delay=DELAY,                 # moderatly responsive
            nre=NRE):                    # optimum durability

        RAID.__init__(self, disk, volumes=volumes, recovery=recovery,
                      delay=delay, nre=nre)
        self.parity = 1
        self.description = "RAID-5: %d+%d" % (volumes - 1, 1)


class RAID6(RAID):
    """ model a RAID set with two parity volumes """

    def __init__(self, disk, volumes=8,  # default 6+2
            recovery=RECOVER / 6,        # recovery from six volumes
            delay=DELAY,                 # moderatly responsive
            nre=NRE):                    # optimum durability

        RAID.__init__(self, disk, volumes=volumes, recovery=recovery,
                      delay=delay, nre=nre)
        self.parity = 2
        self.description = "RAID-6: %d+%d" % (volumes - 2, 2)
