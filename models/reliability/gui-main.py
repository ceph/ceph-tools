#!/usr/bin/python
#
# GUI for driving reliability simulations
#

import RelyFuncts
import SiteRely
import DiskRely
import RaidRely
import RadosRely
import MultiSite

import TestConfig
import TestRun

import RelyGUI


def simdisk():
    """ this function is invoked when the disk COMPUTE button is clicked
    """

    gui.CfgInfo(cfg)    # gather all of the configuration info
    t = cfg.period
    p = False if cfg.parms == 0 else True
    h = False if cfg.headings == 0 else True

    # instantiate the chosen disk
    disk = DiskRely.Disk(size=cfg.disk_size, fits=cfg.disk_fit,
                        nre=cfg.disk_nre,
                        desc="Disk: %s" % (cfg.disk_type))
    TestRun.TestRun([disk], period=t, parms=p, headings=h)


def simraid():
    """ this function is invoked when the RAID COMPUTE button is clicked
        collect the parameters, instantiate and run the described
        simulations
    """

    gui.CfgInfo(cfg)    # gather all of the configuration info
    t = cfg.period
    p = False if cfg.parms == 0 else True
    h = False if cfg.headings == 0 else True

    # instantiate the chosen disk
    disk = DiskRely.Disk(size=cfg.disk_size, fits=cfg.disk_fit,
                        nre=cfg.disk_nre,
                        desc="Disk: %s" % (cfg.disk_type))

    # create the RAID simulation
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
    else:
        raid = None

    TestRun.TestRun([raid], period=t, parms=p, headings=h)


def simrados():
    """ this function is invoked when the RADOS COMPUTE button is clicked
    """

    gui.CfgInfo(cfg)    # gather all of the configuration info
    t = cfg.period
    p = False if cfg.parms == 0 else True
    h = False if cfg.headings == 0 else True

    disk = DiskRely.Disk(size=cfg.disk_size, fits=cfg.disk_fit,
                        nre=cfg.disk_nre,
                        desc="Disk: %s" % (cfg.disk_type))

    # create the RADOS simulation
    rados = RadosRely.RADOS(disk, pg=cfg.rados_decluster,
                            copies=cfg.rados_copies,
                            speed=cfg.rados_recover,
                            fullness=cfg.rados_fullness,
                            nre=cfg.nre_meaning,
                            delay=cfg.rados_markout)
    TestRun.TestRun([rados], period=t, parms=p, headings=h,
                    objsize=cfg.obj_size)


def simsites():
    """ this function is invoked when the sites COMPUTE button is clicked
    """

    gui.CfgInfo(cfg)    # gather all of the configuration info
    t = cfg.period
    p = False if cfg.parms == 0 else True
    h = False if cfg.headings == 0 else True
    f = 0 if cfg.majeure == 0 \
        else float(RelyFuncts.BILLION) / cfg.majeure

    # instantiate the chosen disk
    disk = DiskRely.Disk(size=cfg.disk_size, fits=cfg.disk_fit,
                        nre=cfg.disk_nre,
                        desc="Disk: %s" % (cfg.disk_type))

    # create the RADOS simulation
    rados = RadosRely.RADOS(disk, pg=cfg.rados_decluster,
                            copies=cfg.rados_copies,
                            speed=cfg.rados_recover,
                            fullness=cfg.rados_fullness,
                            nre=cfg.nre_meaning,
                            delay=cfg.rados_markout)

    # create the site and multi-site simulations
    site = SiteRely.Site(fits=f, rplc=cfg.site_recover)
    multi = MultiSite.MultiSite(rados, site,
                speed=cfg.remote_recover,
                latency=cfg.remote_latency,
                sites=cfg.remote_sites)

    TestRun.TestRun((site, multi), period=t, parms=p, headings=h,
        objsize=cfg.obj_size)

#
# If I were a better python programmer I probably would have been
# able to figure out how to do this without the globals gui+cfg
#
cfg = TestConfig.TestConfig()
gui = RelyGUI.RelyGUI(cfg, simdisk, simraid, simrados, simsites)
gui.mainloop()
