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
main routine for driving simulations
    process args and invoke gui or a default set of tests
"""

from DiskRely import Disk
from RaidRely import RAID0, RAID1, RAID5, RAID6
from RadosRely import RADOS
from SiteRely import Site
from MultiRely import MultiSite
from Config import Config
from Run import Run


def oneTest(cfg, which):
    """
    run a single simulation (call-back from the GUI)
        cfg -- configuration values to use
        which -- type of simulation to be run
    """

    # everybody needs a disk simulation
    disk = Disk(size=cfg.disk_size,
                        fits=cfg.disk_fit, fits2=cfg.disk_fit2,
                        nre=cfg.disk_nre,
                        desc="Disk: %s" % (cfg.disk_type))

    if which == "disk":
        Run([disk], period=cfg.period, verbosity=cfg.verbose)
        return

    if which == "raid":
        if cfg.raid_type == "RAID-0":
            raid = RAID0(disk, volumes=cfg.raid_vols,
                                  nre_model=cfg.nre_model,
                                  recovery=cfg.raid_recover,
                                  delay=cfg.raid_replace,
                                  objsize=cfg.obj_size)
        elif cfg.raid_type == "RAID-1":
            raid = RAID1(disk, volumes=cfg.raid_vols,
                                  nre_model=cfg.nre_model,
                                  recovery=cfg.raid_recover,
                                  delay=cfg.raid_replace,
                                  objsize=cfg.obj_size)
        elif cfg.raid_type == "RAID-5":
            raid = RAID5(disk, volumes=cfg.raid_vols,
                                  nre_model=cfg.nre_model,
                                  recovery=cfg.raid_recover,
                                  delay=cfg.raid_replace,
                                  objsize=cfg.obj_size)
        elif cfg.raid_type == "RAID-6":
            raid = RAID6(disk, volumes=cfg.raid_vols,
                                  nre_model=cfg.nre_model,
                                  recovery=cfg.raid_recover,
                                  delay=cfg.raid_replace,
                                  objsize=cfg.obj_size)
        Run([raid], period=cfg.period, verbosity=cfg.verbose)
        return

    rados = RADOS(disk, pg=cfg.rados_decluster,
                    copies=cfg.rados_copies,
                    speed=cfg.rados_recover,
                    fullness=cfg.rados_fullness,
                    objsize=cfg.obj_size,
                    stripe=cfg.stripe_length,
                    nre_model=cfg.nre_model,
                    delay=cfg.rados_markout)
    if which == "rados":
        Run([rados], period=cfg.period, verbosity=cfg.verbose)
        return

    if which == "multi":
        site = Site(fits=cfg.majeure, rplc=cfg.site_recover)
        multi = MultiSite(rados, site,
                speed=cfg.remote_recover,
                latency=cfg.remote_latency,
                sites=cfg.remote_sites)
        Run([multi], period=cfg.period, verbosity=cfg.verbose)
        return


def defaultTests(cfg):
    """
    run a standard set of interesting simulations
        cfg -- default configuration values
    """
    disk = Disk(size=cfg.disk_size, fits=cfg.disk_fit,
                        nre=cfg.disk_nre,
                        desc="Disk: %s" % (cfg.disk_type))

    raid0 = RAID0(disk, volumes=2,
                          nre_model=cfg.nre_model,
                          recovery=cfg.raid_recover,
                          delay=cfg.raid_replace,
                          objsize=cfg.obj_size)
    raid1 = RAID1(disk, volumes=2,
                          nre_model=cfg.nre_model,
                          recovery=cfg.raid_recover,
                          delay=cfg.raid_replace,
                          objsize=cfg.obj_size)
    raid5 = RAID5(disk, volumes=4,
                          nre_model=cfg.nre_model,
                          recovery=cfg.raid_recover,
                          delay=cfg.raid_replace,
                          objsize=cfg.obj_size)
    raid6 = RAID6(disk, volumes=8,
                          nre_model=cfg.nre_model,
                          recovery=cfg.raid_recover,
                          delay=cfg.raid_replace,
                          objsize=cfg.obj_size)

    tests = [disk, raid0, raid5, raid1, raid6]

    # single site RADOS
    for cp in (1, 2, 3):
        rados = RADOS(disk, pg=cfg.rados_decluster,
                        copies=cp,
                        speed=cfg.rados_recover,
                        fullness=cfg.rados_fullness,
                        objsize=cfg.obj_size,
                        stripe=cfg.stripe_length,
                        nre_model=cfg.nre_model,
                        delay=cfg.rados_markout)
        tests.append(rados)

    # multi-site RADOS
    tests.append(None)
    site = Site(fits=cfg.majeure, rplc=cfg.site_recover)
    tests.append(site)
    for sites in (1, 2, 3, 4):
        for cp in (1, 2, 3):
            rados = RADOS(disk, pg=cfg.rados_decluster,
                        copies=cp,
                        speed=cfg.rados_recover,
                        fullness=cfg.rados_fullness,
                        objsize=cfg.obj_size,
                        stripe=cfg.stripe_length,
                        nre_model=cfg.nre_model,
                        delay=cfg.rados_markout)

            multi = MultiSite(rados, site,
                    speed=cfg.remote_recover,
                    latency=cfg.remote_latency,
                    sites=sites)
            tests.append(multi)

    # and run them all
    Run(tests, period=cfg.period, verbosity=cfg.verbose)


def main():
    """ CLI entry-point:
        process command line arguments, run gui or a standard set of tests
    """

    # process the command line arguments arguments
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option("-g", "--gui", dest="gui", action="store_true",
                default=False, help="GUI control panel")
    (opts, files) = parser.parse_args()

    for f in files:
        if f == "gui" or f == "GUI":
            opts.gui = True

    # default configuration parameters
    cfg = Config()
    if opts.gui:     # use the GUI to control the computations
        from RelyGUI import RelyGUI
        gui = RelyGUI(cfg, oneTest)
        gui.mainloop()
    else:       # run a stanadrd set of models
        defaultTests(cfg)


if __name__ == "__main__":
    main()
