#!/usr/bin/python
#
# GUI for driving reliability simulations
#

import RelyFuncts
import DiskRely
import RaidRely
import RadosRely

import TestConfig
import TestRun

import RelyGUI


def simulate():
    """ this function is invoked when the COMPUTE button is clicked
        collect the parameters, instantiate and run the described
        simulations
    """

    gui.CfgInfo(cfg)    # gather all of the configuration info

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

    # create the RADOS simulation
    rados = RadosRely.RADOS(disk, pg=cfg.rados_decluster,
                            copies=cfg.rados_copies,
                            speed=cfg.rados_recover,
                            nre=cfg.nre_meaning,
                            delay=cfg.rados_markout)

    TestRun.TestRun((disk, raid, rados),
        period=cfg.period, objsize=cfg.obj_size)


#
# If I were a better python programmer I probably would have been
# able to figure out how to do this without the globals gui+cfg
#
cfg = TestConfig.TestConfig()
gui = RelyGUI.RelyGUI(cfg, simulate)
gui.mainloop()
