#!/usr/bin/python
#
# exerciser for storage reliability models
#

import sys

import RelyFuncts
import DiskRely
import RaidRely
import RadosRely

import TestConfig

import RelyGUI

KB = 1000
MB = KB * 1000
GB = MB * 1000
TB = GB * 1000
PB = TB * 1000


def runTests(tests, raid=None, rados=None, period=RelyFuncts.YEAR):
    """ run and report a set of specified simulations
        tests -- actual list of simulations to run
        disk -- disk simulation (for parameter reporting)
        raid -- raid simulation (for parameter reporting)
        rados --- rados simulation (for parameter reporting)
    """

    print("")
    print("Disk Modeling Parameters")
    print("    size:      %dGB" % (rados.disk.size / GB))
    print("    FIT rate:  %d (%f/year)" % \
          (rados.disk.fits, rados.disk.p_failure(period=RelyFuncts.YEAR)))
    print("    NRE rate:  %6.2E" % (rados.disk.nre))

    vol_per_pb = PB / rados.disk.size

    print("RAID parameters")
    print("    recovery speed:   %d MB/s" % (raid.speed / MB))
    print("    replacement time: %d hours" % (raid.delay))
    print("    rebuild time: %5.2f hours" % (raid.rebuild_time()))
    print("    scrubbing:        %s" % ("True" if raid.scrub else "False"))

    print("RADOS parameters")
    print("    recovery speed: %d MB/s" % (rados.speed / MB))
    print("    markout time:   %d minutes" % (rados.delay * 60))
    print("    recovery time: %5.2f hours" % (rados.rebuild_time()))
    print("    declustering:   %d /osd" % (rados.pgs))

    hfmt = "    %-20s %12s %12s %12s"
    dfmt = "    %-20s %11.6f%% %12.2E %12.2E"
    print("")

    print("Expected failures, data loss (per drive, per PB) in %4.1f years" \
                    % (period / RelyFuncts.YEAR))
    print(hfmt % ("storage", "fail/drive", "bytes/drive", "bytes/PB"))
    print(hfmt % ("--------", "--------", "--------", "--------"))

    # expected data loss due to single drive failures
    for d in tests:
        p_fail = d.p_failure(period=period)
        loss_d = p_fail * d.loss()
        loss_p = loss_d * vol_per_pb
        print(dfmt % (d.description, p_fail * 100, loss_d, loss_p))


#
# If I were a better python programmer I probably would have been
# able to figure out how to do this without the globals gui+cfg
#
def simulate():
    """ this function is invoked when the COMPUTE button is clicked
        collect the parameters, instantiate and run the described
        simulations
    """

    gui.CfgInfo(cfg)    # gather all of the configuration info

    # instantiate the chosen disk
    if cfg.disk_type == "Enterprise":
        disk = DiskRely.EnterpriseDisk(size=cfg.disk_size)
    elif cfg.disk_type == "Consumer":
        disk = DiskRely.ConsumerDisk(size=cfg.disk_size)
    elif cfg.disk_type == "Real":
        disk = DiskRely.RealDisk(size=cfg.disk_size)
    else:
        disk = None

    # create the RAID simulation
    if cfg.raid_type == "RAID-1":
        raid = RaidRely.RAID1(disk, volumes=cfg.raid_vols, \
                              scrub=cfg.raid_scrub, \
                              recovery=cfg.raid_recover, \
                              delay=cfg.raid_replace)
    elif cfg.raid_type == "RAID-5":
        raid = RaidRely.RAID5(disk, volumes=cfg.raid_vols, \
                              scrub=cfg.raid_scrub, \
                              recovery=cfg.raid_recover, \
                              delay=cfg.raid_replace)
    elif cfg.raid_type == "RAID-6":
        raid = RaidRely.RAID6(disk, volumes=cfg.raid_vols, \
                              scrub=cfg.raid_scrub, \
                              recovery=cfg.raid_recover, \
                              delay=cfg.raid_replace)
    else:
        raid = None

    # create the RADOS simulation
    rados = RadosRely.RADOS(disk, pg=cfg.rados_decluster, \
                            copies=cfg.rados_copies, \
                            speed=cfg.rados_recover, \
                            delay=cfg.rados_markout)

    runTests((disk, raid, rados), raid=raid, rados=rados, period=cfg.period)

# figure out whether we are GUI or default
if len(sys.argv) > 1 and sys.argv[1] == '--help':
    print("Usage: cmd [gui] [test]")
    sys.exit(0)

cfg = TestConfig.TestConfig()

if len(sys.argv) == 1 or sys.argv[1] == "gui":
    gui = RelyGUI.RelyGUI(cfg, simulate)
    gui.mainloop()
else:
    # standard set of tests
    # cfg.FixTimes()
    disk = DiskRely.EnterpriseDisk(size=cfg.disk_size)
    raid1 = RaidRely.RAID1(disk, recovery=cfg.raid_recover, \
                           delay=cfg.raid_replace)
    raid5 = RaidRely.RAID5(disk, recovery=cfg.raid_recover, \
                           delay=cfg.raid_replace)
    raid6 = RaidRely.RAID6(disk, recovery=cfg.raid_recover, \
                           delay=cfg.raid_replace)
    rados2 = RadosRely.RADOS(disk, copies=cfg.rados_copies, \
                             speed=cfg.rados_recover, \
                             delay=cfg.rados_markout)
    rados3 = RadosRely.RADOS(disk, copies=3, speed=cfg.rados_recover, \
                             delay=cfg.rados_markout)

    # now run those tests
    runTests((disk, raid1, raid5, raid6, rados2, rados3), \
             raid=raid1, rados=rados2, period=cfg.period)
