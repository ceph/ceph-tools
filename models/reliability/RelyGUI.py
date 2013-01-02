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
        "Enterprise", "Consumer  ", "Real      "
    ]

    nre_rates = [       # list of likely NRE rates ... correspond to above
        "1.0E-15", "1.0E-14", "1.0E-13"
    ]

    fit_rates = [       # list of FIT rates ... correspond to the above
        826, 1320, 7800
    ]

    raidTypes = [       # menu of RAID types
        "RAID-1", "RAID-5", "RAID-6"
    ]
    raid_volcount = [   # dflt vols per raid group ... correspond to above
        2, 3, 6
    ]

    nreTypes = [      # ways of modeling NREs
        "NRE = ignore",  "NRE = error", "NRE = fail  "
    ]

    replace_times = [   # list of likely drive replacement times (hours)
        0, 1, 2, 4, 6, 8, 10, 12, 18, 24
    ]

    markout_times = [  # list of likely OSD mark-down times (minutes)
        0, 1, 2, 3, 4, 5, 10, 15, 20, 30, 45, 60
    ]

    rebuild_speeds = [  # list of likely rebuild speeds (MB/s)
        1,  2, 5, 10, 20, 25, 40, 50, 60, 80, 100, 120, 140, 160
    ]

    # GUI widget field widths
    short_wid = 2
    med_wid = 4
    long_wid = 6
    short_fmt = "%2d"
    med_fmt = "%4d"
    long_fmt = "%6d"

    # references to the input widget fields (I know ...)
    disk_type = None
    disk_size = None
    disk_fit = None
    disk_nre = None
    raid_type = None
    raid_rplc = None
    raid_speed = None
    raid_vols = None
    rados_pgs = None
    rados_cpys = None
    rados_down = None
    rados_speed = None
    period = None
    nre_meaning = None

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
        OptionMenu(t, self.disk_type, *self.diskTypes, \
                    command=self.diskchoice).grid(column=1, row=2)
        Label(t).grid(column=1, row=3)
        Label(t, text="Size (GB)").grid(column=1, row=4)
        self.disk_size = Entry(t, width=self.long_wid)
        self.disk_size.delete(0, END)
        self.disk_size.insert(0, self.long_fmt % (cfg.disk_size / GB))
        self.disk_size.grid(column=1, row=5)
        Label(t).grid(column=1, row=6)
        Label(t, text="FITs").grid(column=1, row=7)
        self.disk_fit = Entry(t, width=self.long_wid)
        self.disk_fit.delete(0, END)
        self.disk_fit.insert(0, self.fit_rates[0])
        self.disk_fit.grid(column=1, row=8)
        Label(t).grid(column=1, row=9)
        Label(t, text="NRE rate").grid(column=1, row=10)
        self.disk_nre = Spinbox(t, width=self.long_wid, values=self.nre_rates)
        self.disk_nre.grid(column=1, row=11)

        # center stack (RAID)
        Label(t, text="RAID Type").grid(column=2, row=1)
        self.raid_type = StringVar(t)
        self.raid_type.set(self.raidTypes[0])
        OptionMenu(t, self.raid_type, *self.raidTypes, \
                   command=self.raidchoice).grid(column=2, row=2)
        Label(t).grid(column=2, row=3)
        Label(t, text="Replacement (hours)").grid(column=2, row=4)
        self.raid_rplc = Spinbox(t, width=self.short_wid, \
                    values=self.replace_times)
        self.raid_rplc.grid(column=2, row=5)
        self.raid_rplc.delete(0, END)
        self.raid_rplc.insert(0, "%d" % cfg.raid_replace)
        Label(t).grid(column=2, row=6)
        Label(t, text="Rebuild (MB/s)").grid(column=2, row=7)
        self.raid_speed = Spinbox(t, width=self.med_wid, \
                    values=self.rebuild_speeds)
        self.raid_speed.grid(column=2, row=8)
        self.raid_speed.delete(0, END)
        self.raid_speed.insert(0, "%d" % (cfg.raid_recover / MB))
        Label(t).grid(column=2, row=9)
        Label(t, text="Volumes").grid(column=2, row=10)
        self.raid_vols = Spinbox(t, from_=2, to=10, width=self.short_wid)
        self.raid_vols.grid(column=2, row=11)

        # right stack (RADOS)
        Label(t, text="RADOS copies").grid(column=3, row=1)
        self.rados_cpys = Spinbox(t, values=(1, 2, 3), width=self.short_wid)
        self.rados_cpys.grid(column=3, row=2)
        self.rados_cpys.delete(0, END)
        self.rados_cpys.insert(0, "%d" % cfg.rados_copies)
        Label(t).grid(column=3, row=3)
        Label(t, text="Mark-out (minutes)").grid(column=3, row=4)
        self.rados_down = Spinbox(t, values=self.markout_times, \
                    width=self.short_wid)
        self.rados_down.grid(column=3, row=5)
        self.rados_down.delete(0, END)
        self.rados_down.insert(0, "%d" % (cfg.rados_markout * 60))
        Label(t).grid(column=3, row=6)
        Label(t, text="Recovery (MB/s)").grid(column=3, row=7)
        self.rados_speed = Spinbox(t, width=self.med_wid, \
                    values=self.rebuild_speeds)
        self.rados_speed.grid(column=3, row=8)
        self.rados_speed.delete(0, END)
        self.rados_speed.insert(0, "%d" % (cfg.rados_recover / MB))
        Label(t).grid(column=3, row=9)
        Label(t, text="Declustering").grid(column=3, row=10)
        self.rados_pgs = Entry(t, width=self.med_wid)
        self.rados_pgs.delete(0, END)
        self.rados_pgs.insert(0, self.med_fmt % cfg.rados_decluster)
        self.rados_pgs.grid(column=3, row=11)

        # and finally the bottom "doit" controls
        Label(t, text="Period (years)").grid(column=1, row=12)
        self.period = Spinbox(t, from_=1, to=10, width=self.short_wid)
        self.period.grid(column=1, row=13)
        self.nre_meaning = StringVar(t)
        self.nre_meaning.set(self.nreTypes[0])
        OptionMenu(t, self.nre_meaning, *self.nreTypes).grid(column=2, row=13)
        Button(t, text="COMPUTE", command=doit).grid(column=3, row=13)
        Label(t).grid(column=1, row=14)

        self.root = t

    def diskchoice(self, value):
        """ change default FIT and NRE rates to match disk selection """
        self.disk_nre.delete(0, END)
        self.disk_fit.delete(0, END)
        i = 0
        while i < len(self.diskTypes):
            if value == self.diskTypes[i]:
                self.disk_nre.insert(0, self.nre_rates[i])
                self.disk_fit.insert(0, self.fit_rates[i])
                return
            i += 1

    def raidchoice(self, value):
        """ change default # of volumes to match RAID levels """
        self.raid_vols.delete(0, END)
        i = 0
        while i < len(self.raidTypes):
            if value == self.raidTypes[i]:
                self.raid_vols.insert(0, self.raid_volcount[i])
                return
            i += 1

    def CfgInfo(self, cfg):
        """ scrape configuration information out of the widgets """
        cfg.period = 365.25 * 24 * int(self.period.get())
        cfg.disk_type = self.disk_type.get()
        cfg.disk_size = int(self.disk_size.get()) * GB
        cfg.disk_nre = float(self.disk_nre.get())
        cfg.disk_fit = int(self.disk_fit.get())
        cfg.raid_vols = int(self.raid_vols.get())
        cfg.raid_type = self.raid_type.get()
        cfg.raid_replace = int(self.raid_rplc.get())
        cfg.raid_recover = int(self.raid_speed.get()) * MB
        cfg.rados_copies = int(self.rados_cpys.get())
        cfg.rados_markout = float(self.rados_down.get()) / 60
        cfg.rados_recover = int(self.rados_speed.get()) * MB
        cfg.rados_decluster = int(self.rados_pgs.get())
        i = 0
        while i < len(self.nreTypes):
            if self.nre_meaning.get() == self.nreTypes[i]:
                cfg.nre_meaning = i
                return
            i += 1

    def mainloop(self):
        self.root.mainloop()
