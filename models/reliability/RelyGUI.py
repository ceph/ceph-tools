#!/usr/bin/python
#
# GUI for setting reliability model parameters

from Tkinter import *

# CONVENIENT UNITS
MB = 1000000
GB = MB * 1000


# Let me apologize in advance for this brute-force GUI.
# Not being a python programmer, I've never seen how it
# is supposed to be done.
class RelyGUI:
    """ GUI for driving storage reliability simulations """

    diskTypes = [       # menu of disk drive types
        "Enterprise",
        "Consumer",
        "Real"
    ]
    raidTypes = [       # menu of RAID types
        "RAID-1",
        "RAID-5",
        "RAID-6"
    ]
    scrubTypes = [      # menu of scrub types
        "w/o scrub",
        "w/scrub"
    ]

    replace_times = [   # list of likely drive replacement times (hours)
        0, 1, 2, 4, 6, 8, 10, 12, 18, 24
    ]

    markout_times = [  # list of likely OSD mark-down times (minutes)
        0, 1, 2, 3, 4, 5, 10, 15, 20
    ]

    rebuild_speeds = [  # list of likely rebuild speeds (MB/s)
        1, 2, 5, 10, 20, 25, 40, 50, 60, 80, 100, 120, 140
    ]

    # references to the input widget fields (I know ...)
    disk_type = None
    disk_size = None
    raid_type = None
    raid_rplc = None
    raid_speed = None
    raid_vols = None
    rados_pgs = None
    rados_cpys = None
    rados_down = None
    rados_speed = None
    period = None
    scrubbing = None

    def __init__(self, cfg, doit):
        """ create a GUI panel
            cfg -- default parameter values
            doit -- call back for compute button
            """

        t = Tk()
        t.title('Data Reliability Model')
        # t.iconbitmap(default='inktank.ico')   # ? windows only ?

        # left stack (DISK)
        Label(t, text="Disk Type").grid(column=1, row=1)
        self.disk_type = StringVar(t)
        self.disk_type.set(self.diskTypes[0])
        OptionMenu(t, self.disk_type, *self.diskTypes).grid(column=1, row=2)
        Label(t).grid(column=1, row=3)
        Label(t, text="Size (GB)").grid(column=1, row=4)
        self.disk_size = Entry(t, width=10)
        self.disk_size.insert(0, "%d" % (cfg.disk_size / GB))
        self.disk_size.grid(column=1, row=5)

        # center stack (RAID)
        Label(t, text="RAID Type").grid(column=2, row=1)
        self.raid_type = StringVar(t)
        self.raid_type.set(self.raidTypes[0])
        OptionMenu(t, self.raid_type, *self.raidTypes, \
                   command=self.raidchoice).grid(column=2, row=2)
        Label(t).grid(column=2, row=3)
        Label(t, text="Replacement (hours)").grid(column=2, row=4)
        self.raid_rplc = Spinbox(t, width=3, values=self.replace_times)
        self.raid_rplc.grid(column=2, row=5)
        self.raid_rplc.delete(0)
        self.raid_rplc.insert(0, "%d" % cfg.raid_replace)
        Label(t).grid(column=2, row=6)
        Label(t, text="Rebuild (MB/s)").grid(column=2, row=7)
        self.raid_speed = Spinbox(t, width=4, values=self.rebuild_speeds)
        self.raid_speed.grid(column=2, row=8)
        self.raid_speed.delete(0)
        self.raid_speed.insert(0, "%d" % (cfg.raid_recover / MB))
        Label(t).grid(column=2, row=9)
        Label(t, text="Volumes").grid(column=2, row=10)
        self.raid_vols = Spinbox(t, from_=2, to=10, width=3)
        self.raid_vols.grid(column=2, row=11)

        # right stack (RADOS)
        Label(t, text="RADOS copies").grid(column=3, row=1)
        self.rados_cpys = Spinbox(t, values=(1, 2, 3), width=2)
        self.rados_cpys.grid(column=3, row=2)
        self.rados_cpys.delete(0)
        self.rados_cpys.insert(0, "%d" % cfg.rados_copies)
        Label(t).grid(column=3, row=3)
        Label(t, text="Mark-out (minutes)").grid(column=3, row=4)
        self.rados_down = Spinbox(t, values=self.markout_times, width=3)
        self.rados_down.grid(column=3, row=5)
        self.rados_down.delete(0)
        self.rados_down.insert(0, "%d" % (cfg.rados_markout * 60))
        Label(t).grid(column=3, row=6)
        Label(t, text="Recovery (MB/s)").grid(column=3, row=7)
        self.rados_speed = Spinbox(t, width=4, values=self.rebuild_speeds)
        self.rados_speed.grid(column=3, row=8)
        self.rados_speed.delete(0)
        self.rados_speed.insert(0, "%d" % (cfg.rados_recover / MB))
        Label(t).grid(column=3, row=9)
        Label(t, text="Declustering").grid(column=3, row=10)
        self.rados_pgs = Entry(t, width=10)
        self.rados_pgs.insert(0, "%d" % cfg.rados_decluster)
        self.rados_pgs.grid(column=3, row=11)

        # and finally the bottom "doit" controls
        Label(t, text="Period (years)").grid(column=1, row=12)
        self.period = Spinbox(t, from_=1, to=10, width=3)
        self.period.grid(column=1, row=13)
        self.scrubbing = StringVar(t)
        self.scrubbing.set(self.scrubTypes[0])
        OptionMenu(t, self.scrubbing, *self.scrubTypes).grid(column=2, row=13)
        Button(t, text="COMPUTE", command=doit).grid(column=3, row=13)
        Label(t).grid(column=1, row=14)

        self.root = t

    def raidchoice(self, value):
        """ change default # of volumes to match RAID levels """
        s = self.raid_type.get()
        if s == "RAID-1":
            self.raid_vols.delete(0)
            self.raid_vols.insert(0, 2)
        elif s == "RAID-5":
            self.raid_vols.delete(0)
            self.raid_vols.insert(0, 3)
        elif s == "RAID-6":
            self.raid_vols.delete(0)
            self.raid_vols.insert(0, 6)

    def CfgInfo(self, cfg):
        """ scrape configuration information out of the widgets """
        cfg.period = 365.25 * 24 * int(self.period.get())
        cfg.disk_type = self.disk_type.get()
        cfg.disk_size = int(self.disk_size.get()) * GB
        cfg.raid_vols = int(self.raid_vols.get())
        cfg.raid_type = self.raid_type.get()
        cfg.raid_replace = int(self.raid_rplc.get())
        cfg.raid_reccover = int(self.raid_speed.get()) * MB
        cfg.raid_scrub = self.scrubbing.get() == self.scrubTypes[1]
        cfg.rados_copies = int(self.rados_cpys.get())
        cfg.rados_markout = float(self.rados_down.get()) / 60
        cfg.rados_recover = int(self.rados_speed.get()) * MB
        cfg.rados_decluster = int(self.rados_pgs.get())

    def mainloop(self):
        self.root.mainloop()
