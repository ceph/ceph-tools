#!/usr/bin/python
#
# GUI for setting reliability model parameters

from Tkinter import *

# CONVENIENT UNITS
MB = 1000000
GB = MB * 1000
TB = GB * 1000


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
        "ignore",  "error", "fail", "ignore+fail/2"
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

    async_latencies = [  # list of likely asynchronous replication latencies
        0, 1, 5, 10, 20, 50, 100, 200, 500, 1000, 5000, 10000, 50000, 100000
    ]

    fullness = [    # list of likely volume fullness percentages
        50, 75, 80, 85, 90, 95
    ]

    site_count = [  # list of likely remote site numbers
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    ]

    remote_speeds = [   # list of likely remote recovery speeds (MB/s)
        1,  2, 5, 10, 20, 25, 40, 50, 60, 80, 100, 150,
        200, 300, 400, 500, 600, 800, 1000
    ]

    site_destroy = [    # force majeure event frequency
        "never", 10, 100, 1000, 10000, 100000
    ]

    site_recover = [    # number of hours to replace a destroyed facility
        1, 6, 12, 24, 30 * 24, 6 * 30 * 24, int(365.25 * 24)
    ]

    site_avails = [     # plausible site availabilities
        "0.8", "0.9", "0.99", "0.999", "0.9999", "0.9999", "1.0"
    ]

    object_sizes = []       # generate this one dynamically
    min_obj_size = 1 * MB
    max_obj_size = 1 * TB

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
    site_num = None
    remote_speed = None
    remote_rplc = None
    remote_fail = None
    period = None
    nre_meaning = None
    obj_size = None

    def __init__(self, cfg, doit):
        """ create a GUI panel
            cfg -- default parameter values
            doit -- call back for compute button
            """

        t = Tk()
        t.title('Data Reliability Model')
        # t.iconbitmap(default='inktank.ico')   # ? windows only ?

        # a few layout constants to make things a little clearer
        c_disk = 1
        c_raid = 2
        c_rados = 3
        c_site = 4
        bottom = 20

        # left stack (DISK)
        Label(t, text="Disk Type").grid(column=c_disk, row=1)
        self.disk_type = StringVar(t)
        self.disk_type.set(self.diskTypes[0])
        OptionMenu(t, self.disk_type, *self.diskTypes, \
                    command=self.diskchoice).grid(column=c_disk, row=2)
        Label(t).grid(column=c_disk, row=3)
        Label(t, text="Size (GB)").grid(column=c_disk, row=4)
        self.disk_size = Entry(t, width=self.long_wid)
        self.disk_size.delete(0, END)
        self.disk_size.insert(0, self.long_fmt % (cfg.disk_size / GB))
        self.disk_size.grid(column=c_disk, row=5)
        Label(t).grid(column=c_disk, row=6)
        Label(t, text="FITs").grid(column=c_disk, row=7)
        self.disk_fit = Entry(t, width=self.long_wid)
        self.disk_fit.delete(0, END)
        self.disk_fit.insert(0, self.fit_rates[0])
        self.disk_fit.grid(column=c_disk, row=8)
        Label(t).grid(column=c_disk, row=9)
        Label(t, text="NRE rate").grid(column=c_disk, row=10)
        self.disk_nre = Spinbox(t, width=self.long_wid, values=self.nre_rates)
        self.disk_nre.grid(column=c_disk, row=11)
        Label(t).grid(column=c_disk, row=12)
        Label(t, text="node FITS").grid(column=c_disk, row=13)
        self.node_fit = Entry(t, width=self.long_wid)
        self.node_fit.delete(0, END)
        self.node_fit.insert(0, cfg.node_fit)
        self.node_fit.grid(column=c_disk, row=14)
        Label(t).grid(column=c_disk, row=15)
        Label(t).grid(column=c_disk, row=16)
        Label(t, text="Period (years)").grid(column=c_disk, row=bottom - 3)
        self.period = Spinbox(t, from_=1, to=10, width=self.short_wid)
        self.period.grid(column=c_disk, row=bottom - 2)

        # center stack (RAID)
        Label(t, text="RAID Type").grid(column=c_raid, row=1)
        self.raid_type = StringVar(t)
        self.raid_type.set(self.raidTypes[0])
        OptionMenu(t, self.raid_type, *self.raidTypes,
                   command=self.raidchoice).grid(column=c_raid, row=2)
        Label(t).grid(column=c_raid, row=3)
        Label(t, text="Replace (hours)").grid(column=c_raid, row=4)
        self.raid_rplc = Spinbox(t, width=self.short_wid,
                    values=self.replace_times)
        self.raid_rplc.grid(column=c_raid, row=5)
        self.raid_rplc.delete(0, END)
        self.raid_rplc.insert(0, "%d" % cfg.raid_replace)
        Label(t).grid(column=c_raid, row=6)
        Label(t, text="Rebuild (MB/s)").grid(column=c_raid, row=7)
        self.raid_speed = Spinbox(t, width=self.med_wid,
                    values=self.rebuild_speeds)
        self.raid_speed.grid(column=c_raid, row=8)
        self.raid_speed.delete(0, END)
        self.raid_speed.insert(0, "%d" % (cfg.raid_recover / MB))
        Label(t).grid(column=c_raid, row=9)
        Label(t, text="Volumes").grid(column=c_raid, row=10)
        self.raid_vols = Spinbox(t, from_=2, to=10, width=self.short_wid)
        self.raid_vols.grid(column=c_raid, row=11)
        Label(t).grid(column=c_raid, row=12)
        Label(t).grid(column=c_raid, row=bottom - 4)
        Label(t, text="NRE model").grid(column=c_raid, row=bottom - 3)
        self.nre_meaning = StringVar(t)
        self.nre_meaning.set(self.nreTypes[0])
        OptionMenu(t, self.nre_meaning, *self.nreTypes).grid(column=c_raid,
                                                row=bottom - 2)

        # right stack (RADOS)
        Label(t, text="RADOS copies").grid(column=c_rados, row=1)
        self.rados_cpys = Spinbox(t, values=(1, 2, 3, 4, 5, 6),
            width=self.short_wid)
        self.rados_cpys.grid(column=c_rados, row=2)
        self.rados_cpys.delete(0, END)
        self.rados_cpys.insert(0, "%d" % cfg.rados_copies)
        Label(t).grid(column=c_rados, row=3)
        Label(t, text="Mark-out (min)").grid(column=c_rados, row=4)
        self.rados_down = Spinbox(t, values=self.markout_times,
                    width=self.short_wid)
        self.rados_down.grid(column=c_rados, row=5)
        self.rados_down.delete(0, END)
        self.rados_down.insert(0, "%d" % (cfg.rados_markout * 60))
        Label(t).grid(column=c_rados, row=6)
        Label(t, text="Recovery (MB/s)").grid(column=c_rados, row=7)
        self.rados_speed = Spinbox(t, width=self.med_wid,
                    values=self.rebuild_speeds)
        self.rados_speed.grid(column=c_rados, row=8)
        self.rados_speed.delete(0, END)
        self.rados_speed.insert(0, "%d" % (cfg.rados_recover / MB))
        Label(t).grid(column=c_rados, row=9)
        Label(t, text="Usage (%)").grid(column=c_rados, row=10)
        self.rados_fullness = Spinbox(t, values=self.fullness,
                    width=self.med_wid)
        self.rados_fullness.grid(column=c_rados, row=11)
        self.rados_fullness.delete(0, END)
        self.rados_fullness.insert(0, "%d" % (cfg.rados_fullness * 100))
        Label(t).grid(column=c_rados, row=12)
        Label(t, text="Declustering").grid(column=c_rados, row=13)
        self.rados_pgs = Entry(t, width=self.med_wid)
        self.rados_pgs.delete(0, END)
        self.rados_pgs.insert(0, self.med_fmt % cfg.rados_decluster)
        self.rados_pgs.grid(column=c_rados, row=14)
        Label(t).grid(column=c_rados, row=15)
        Label(t).grid(column=c_rados, row=bottom - 4)
        Label(t, text="Object size").grid(column=c_rados, row=bottom - 3)

        # generate this list dynamically
        os = self.min_obj_size
        while os <= self.max_obj_size:
            if os < MB:
                s = "%dKB" % (os / KB)
            elif os < GB:
                s = "%dMB" % (os / MB)
            elif os < TB:
                s = "%dGB" % (os / GB)
            else:
                s = "%dTB" % (os / TB)
            self.object_sizes.append(s)
            os *= 10
        self.obj_size = StringVar(t)
        self.obj_size.set(self.object_sizes[0])
        OptionMenu(t, self.obj_size, *self.object_sizes).grid(column=c_rados,
                                                row=bottom - 2)

        # fourth stack (remote site)
        Label(t, text="Sites").grid(column=c_site, row=1)
        self.site_num = Spinbox(t, values=self.site_count,
            width=self.short_wid)
        self.site_num.grid(column=c_site, row=2)
        self.site_num.delete(0, END)
        self.site_num.insert(0, "%d" % cfg.remote_sites)
        Label(t).grid(column=c_site, row=3)
        Label(t, text="Availability").grid(column=c_site, row=4)
        self.remote_avail = Spinbox(t, values=self.site_avails,
            width=self.long_wid)
        self.remote_avail.grid(column=c_site, row=5)
        self.remote_avail.delete(0, END)
        self.remote_avail.insert(0, "%6.4f" % cfg.remote_avail)
        Label(t).grid(column=c_site, row=6)
        Label(t, text="Recovery (MB/s)").grid(column=c_site, row=7)
        self.remote_speed = Spinbox(t, values=self.remote_speeds,
            width=self.med_wid)
        self.remote_speed.grid(column=c_site, row=8)
        self.remote_speed.delete(0, END)
        self.remote_speed.insert(0, "%d" % (cfg.remote_recover / MB))
        Label(t).grid(column=c_site, row=9)
        Label(t, text="Rep Latency (ms)").grid(column=c_site, row=10)
        self.rados_latency = Spinbox(t, values=self.async_latencies,
                    width=self.med_wid)
        self.rados_latency.grid(column=c_site, row=11)
        self.rados_latency.delete(0, END)
        self.rados_latency.insert(0, "%d" % (cfg.rados_latency))
        Label(t).grid(column=c_site, row=12)
        Label(t, text="Disaster (years)").grid(column=c_site, row=bottom - 3)
        self.remote_fail = StringVar(t)
        self.remote_fail.set(self.site_destroy[0])
        OptionMenu(t, self.remote_fail, *self.site_destroy).grid(column=c_site,
                                                                row=bottom - 2)

        # and finally the bottom "doit" button
        Label(t).grid(column=c_raid, row=bottom - 1)
        Button(t, text="COMPUTE", command=doit).grid(column=2, row=bottom)
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
        cfg.node_fit = int(self.node_fit.get())
        cfg.raid_vols = int(self.raid_vols.get())
        cfg.raid_type = self.raid_type.get()
        cfg.raid_replace = int(self.raid_rplc.get())
        cfg.raid_recover = int(self.raid_speed.get()) * MB
        cfg.nre_meaning = self.nre_meaning.get()
        cfg.rados_copies = int(self.rados_cpys.get())
        cfg.rados_markout = float(self.rados_down.get()) / 60
        cfg.rados_recover = int(self.rados_speed.get()) * MB
        cfg.rados_decluster = int(self.rados_pgs.get())
        cfg.rados_fullness = float(self.rados_fullness.get()) / 100
        cfg.rados_latency = int(self.rados_latency.get())
        cfg.remote_sites = int(self.site_num.get())
        cfg.remote_avail = float(self.remote_avail.get())
        cfg.remote_recover = int(self.remote_speed.get()) * MB

        cfg.majeure = self.remote_fail.get()
        if self.remote_fail.get() == "never":
            cfg.majeure = 0
        else:
            cfg.majeure = int(self.remote_fail.get()) * 365.25 * 24

        cfg.obj_size = self.min_obj_size
        i = 0
        while i < len(self.object_sizes) and cfg.obj_size < self.max_obj_size:
            if self.obj_size.get() == self.object_sizes[i]:
                break
            cfg.obj_size *= 10
            i += 1

    def mainloop(self):
        self.root.mainloop()
