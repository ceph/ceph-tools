#!/usr/bin/python
#
# reliability simulation driver
#


def simulate(cfg, todo):
    """ this function is invoked to run a specified set of simulations
        with a specified set of parameters
        cfg -- configuration parameters
        todo -- simulations to run
    """

    tests = []
    t = cfg.period
    p = False if cfg.parms == 0 else True
    h = False if cfg.headings == 0 else True

    # instantiate the chosen disk
    import DiskRely
    disk = DiskRely.Disk(size=cfg.disk_size, fits=cfg.disk_fit,
                        nre=cfg.disk_nre,
                        desc="Disk: %s" % (cfg.disk_type))
    if "disk" in todo:
        tests.append(disk)

    # create the RAID simulation
    if "raid" in todo:
        import RaidRely
        if cfg.raid_type == "RAID-1":
            raid = RaidRely.RAID1(disk, volumes=cfg.raid_vols,
                                  nre=cfg.nre_meaning,
                                  recovery=cfg.raid_recover,
                                  delay=cfg.raid_replace)
        elif cfg.raid_type == "RAID-5":
            raid = RaidRely.RAID5(disk, volumes=cfg.raid_vols,
                                  nre=cfg.nre_meaning,
                                  recovery=cfg.raid_recover,
                                  delay=cfg.raid_replace)
        elif cfg.raid_type == "RAID-6":
            raid = RaidRely.RAID6(disk, volumes=cfg.raid_vols,
                                  nre=cfg.nre_meaning,
                                  recovery=cfg.raid_recover,
                                  delay=cfg.raid_replace)
        tests.append(raid)

    # create the RADOS simulation
    if "rados" in todo or "multi" in todo or "site" in todo:
        import RadosRely
        rados = RadosRely.RADOS(disk, pg=cfg.rados_decluster,
                            copies=cfg.rados_copies,
                            speed=cfg.rados_recover,
                            fullness=cfg.rados_fullness,
                            nre=cfg.nre_meaning,
                            delay=cfg.rados_markout)
        if "rados" in todo:
            tests.append(rados)

    if "multi" in todo or "site" in todo:
        import SiteRely
        import MultiSite

        # create the site and multi-site simulations
        site = SiteRely.Site(fits=cfg.majeure, rplc=cfg.site_recover)
        multi = MultiSite.MultiSite(rados, site,
                    speed=cfg.remote_recover,
                    latency=cfg.remote_latency,
                    sites=cfg.remote_sites)

        if "site" in todo:
            tests.append(site)
        tests.append(multi)

    # run all the instantiated tests
    import TestRun
    TestRun.TestRun(tests, period=t, parms=p, headings=h,
        objsize=cfg.obj_size, stripe=cfg.stripe_width)


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
    import TestConfig
    cfg = TestConfig.TestConfig()
    if opts.gui:     # use the GUI to control the computations
        import RelyGUI
        gui = RelyGUI.RelyGUI(cfg, simulate)
        gui.mainloop()
    else:       # run a stanadrd set of models

        print("BASIC RELIABILITIES, IGNORING DISASTERS")
        # disk and raid reliability
        cfg.parms = 1
        cfg.headings = 1
        cfg.raid_type = "RAID-1"
        cfg.raid_vols = 2
        simulate(cfg, "disk,raid")
        cfg.parms = 0
        cfg.headings = 0

        speed = cfg.raid_recover
        cfg.raid_type = "RAID-5"
        cfg.raid_vols = 4
        cfg.raid_recover = speed / (cfg.raid_vols - 1)
        simulate(cfg, "raid")
        cfg.raid_type = "RAID-6"
        cfg.raid_vols = 8
        cfg.raid_recover = speed / (cfg.raid_vols - 2)
        simulate(cfg, "raid")

        # single-site RADOS reliability, ignoring site failures
        cfg.disk_nre = 1E-20    # we have scrubbing
        for cp in (2, 3):
            cfg.rados_copies = cp
            simulate(cfg, "rados")

        print("")
        print("MULTI-SITE RELIABILITIES, INCLUDING DISASTERS")

        # multi-site RADOS reliability, with site failures
        cfg.parms = 1
        cfg.headings = 1
        for sites in (1, 2, 3, 4):
            cfg.remote_sites = sites
            for cp in (1, 2, 3):
                cfg.rados_copies = cp
                simulate(cfg, "multi")
                cfg.parms = 0
                cfg.headings = 0

if __name__ == "__main__":
    main()
