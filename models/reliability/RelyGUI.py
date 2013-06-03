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
GUI for playing with reliability model parameters
"""

from Tkinter import *

# speeds and disk sizes
KiB = 1000
MiB = KiB * 1000
GiB = MiB * 1000
TiB = GiB * 1000

# file sizes
KB = 1024
MB = KB * 1024
GB = MB * 1024
TB = GB * 1024


# Let me apologize in advance for this brute-force GUI.
# Not being a python programmer, I've never seen how it
# is supposed to be done.
class RelyGUI:
    """ GUI for driving storage reliability simulations """

    #
    # enumerated values for menus and spin boxes
    #
    disk_type = None
    diskTypes = [       # menu of disk drive types
        "Enterprise", "Consumer", "Real"
    ]

    disk_nre = None
    nre_rates = [       # list of likely NRE rates ... correspond to above
        "1.0E-19", "1.0E-18", "1.0E-17", "1.0E-16", "1.0E-15", "1.0E-14", "1.0E-13"
    ]

    # default FIT rates for various classes of drives
    fit_map = {
        'Enterprise': "826",
        'Consumer': "1320",
        'Real': "7800"
    }

    # default NRE rates for various classes of drives
    nre_map = {
        'Enterprise': "1.0E-16",
        'Consumer': "1.0E-15",
        'Real': "1.0E-14"
    }

    raid_type = None
    raidTypes = [       # menu of RAID types
        "RAID-0", "RAID-1", "RAID-5", "RAID-6"
    ]

    raid_vols = None

    # default volume counts for various RAID configurations
    vol_map = {
        'RAID-0': 1,
        'RAID-1': 2,
        'RAID-5': 3,
        'RAID-6': 6,
    }

    nre_model = None
    nreTypes = [      # ways of modeling NREs
        "ignore",  "error", "fail", "error+fail/2"
    ]

    raid_rplc = None
    replace_times = [   # list of likely drive replacement times (hours)
        0, 1, 2, 4, 6, 8, 10, 12, 18, 24
    ]

    rados_down = None
    markout_times = [  # list of likely OSD mark-down times (minutes)
        0, 1, 2, 3, 4, 5, 10, 15, 20, 30, 45, 60
    ]

    raid_speed = None
    rados_speed = None
    rebuild_speeds = [  # list of likely rebuild speeds (MB/s)
        1,  2, 5, 10, 15, 20, 25, 40, 50, 60, 80, 100, 120, 140, 160
    ]

    remote_latency = None
    async_latencies = [  # list of likely asynchronous replication latencies
        0, 1, 5, 10, 30, 60, 300, 600, 900, 1800, 3600,
        2 * 3600, 6 * 3600, 12 * 3600, 18 * 3600, 24 * 3600
    ]

    rados_fullness = None
    fullness = [    # list of likely volume fullness percentages
        50, 75, 80, 85, 90, 95, 100
    ]

    site_num = None
    site_count = [  # list of likely remote site numbers
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    ]

    remote_speed = None
    remote_speeds = [   # list of likely remote recovery speeds (MB/s)
        1,  2, 5, 10, 20, 25, 40, 50, 60, 80, 100, 150,
        200, 300, 400, 500, 600, 800, 1000
    ]

    remote_fail = None
    site_destroy = [    # force majeure event frequency
        10, 100, 1000, 10000, 100000, "never"
    ]

    remote_rplc = None
    site_recover = [    # number of days to recover a destroyed facility
        1, 2, 4, 8, 12, 16, 20, 30, 40, 50, 60, 80,
        100, 150, 200, 250, 300, 365, "never"
    ]

    verbosities = [    # display verbosity
        "all",
        "parameters",
        "headings",
        "data only"
    ]

    verbosity = None
    period = None
    disk_size = None
    rados_pgs = None
    rados_cpys = None
    stripe_length = None

    # these we generate dynamically
    obj_size = None
    object_sizes = []
    min_obj_size = 1 * 1024 * 1024
    max_obj_size = 1 * 1024 * 1024 * 1024 * 1024
    step_obj_size = 4

    # GUI widget field widths
    ROWS = 20
    BORDER = 5
    short_wid = 2
    med_wid = 4
    long_wid = 6
    short_fmt = "%2d"
    med_fmt = "%4d"
    long_fmt = "%6d"

    # references to the input widget fields (I know ...)

    def do_disk(self):
        """ calculate disk reliability """
        self.getCfgInfo()
        self.doit(self.cfg, "disk")

    def do_raid(self):
        """ calculate raid reliability """
        self.getCfgInfo()
        self.doit(self.cfg, "raid")

    def do_rados(self):
        """ calculate RADOS reliability """
        self.getCfgInfo()
        self.doit(self.cfg, "rados")

    def do_sites(self):
        """ calculate Multi-Site RADOS reliability """
        self.getCfgInfo()
        self.doit(self.cfg, "multi")

    def diskchoice(self, value):
        """ change default FIT and NRE rates to match disk selection """
        self.disk_nre.delete(0, END)
        self.disk_nre.insert(0, self.nre_map[value])
        self.disk_fit.delete(0, END)
        self.disk_fit.insert(0, self.fit_map[value])
        self.disk_fit2.delete(0, END)
        self.disk_fit2.insert(0, self.fit_map[value])

    def raidchoice(self, value):
        """ change default # of volumes to match RAID levels """
        self.raid_vols.delete(0, END)
        self.raid_vols.insert(0, self.vol_map[value])

    def __init__(self, cfg, doit):
        """ create the GUI panel widgets
            cfg -- parameter values (input and output)
            doit -- method to call to run simulations
            """

        # gather the basic parameters
        self.cfg = cfg
        self.doit = doit

        self.root = Tk()
        self.root.title('Data Reliability Model')
        t = Frame(self.root, bd=2 * self.BORDER)
        # w.iconbitmap(default='inktank.ico')   # ? windows only ?

        # left stack (DISK)
        f = Frame(t, bd=self.BORDER, relief=RIDGE)
        r = 1
        Label(f, text="Disk Type").grid(row=r)
        self.disk_type = StringVar(f)
        self.disk_type.set(self.diskTypes[0])
        OptionMenu(f, self.disk_type, *self.diskTypes,
                    command=self.diskchoice).grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Size (GiB)").grid(row=r)
        self.disk_size = Entry(f, width=self.long_wid)
        self.disk_size.delete(0, END)
        self.disk_size.insert(0, self.long_fmt % (cfg.disk_size / GiB))
        self.disk_size.grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Primary FITs").grid(row=r)
        self.disk_fit = Entry(f, width=self.long_wid)
        self.disk_fit.grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Secondary FITs").grid(row=r)
        self.disk_fit2 = Entry(f, width=self.long_wid)
        self.disk_fit2.grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="NRE rate").grid(row=r)
        self.disk_nre = Spinbox(f, width=self.long_wid, values=self.nre_rates)
        self.disk_nre.grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        while r < self.ROWS:
            Label(f).grid(row=r)
            r += 1
        Button(f, text="RELIABILITY", command=self.do_disk).grid(row=r)
        f.grid(column=1, row=1)
        self.diskchoice(self.diskTypes[0])  # set default disk type

        # second stack (RAID)
        f = Frame(t, bd=self.BORDER, relief=RIDGE)
        r = 1
        Label(f, text="RAID Type").grid(row=r)
        self.raid_type = StringVar(f)
        self.raid_type.set("RAID-1")
        OptionMenu(f, self.raid_type, *self.raidTypes,
                   command=self.raidchoice).grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Replace (hours)").grid(row=r)
        self.raid_rplc = Spinbox(f, width=self.short_wid,
                    values=self.replace_times)
        self.raid_rplc.grid(row=r + 1)
        self.raid_rplc.delete(0, END)
        self.raid_rplc.insert(0, "%d" % cfg.raid_replace)
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Rebuild (MiB/s)").grid(row=r)
        self.raid_speed = Spinbox(f, width=self.med_wid,
                    values=self.rebuild_speeds)
        self.raid_speed.grid(row=r + 1)
        self.raid_speed.delete(0, END)
        self.raid_speed.insert(0, "%d" % (cfg.raid_recover / MiB))
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Volumes").grid(row=r)
        self.raid_vols = Spinbox(f, from_=1, to=10, width=self.short_wid)
        self.raid_vols.grid(row=r + 1)
        Label(f).grid(row=r + 2)
        self.raidchoice("RAID-1")   # set default number of volumes
        r += 3
        while r < self.ROWS:
            Label(f).grid(row=r)
            r += 1
        Button(f, text="RELIABILITY", command=self.do_raid).grid(row=r)
        f.grid(column=2, row=1)

        # third stack (RADOS)
        f = Frame(t, bd=self.BORDER, relief=RIDGE)
        r = 1
        Label(f, text="RADOS copies").grid(row=r)
        self.rados_cpys = Spinbox(f, values=(1, 2, 3, 4, 5, 6),
            width=self.short_wid)
        self.rados_cpys.grid(row=r + 1)
        self.rados_cpys.delete(0, END)
        self.rados_cpys.insert(0, "%d" % cfg.rados_copies)
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Mark-out (min)").grid(row=r)
        self.rados_down = Spinbox(f, values=self.markout_times,
                    width=self.short_wid)
        self.rados_down.grid(row=r + 1)
        self.rados_down.delete(0, END)
        self.rados_down.insert(0, "%d" % (cfg.rados_markout * 60))
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Recovery (MiB/s)").grid(row=r)
        self.rados_speed = Spinbox(f, width=self.med_wid,
                    values=self.rebuild_speeds)
        self.rados_speed.grid(row=r + 1)
        self.rados_speed.delete(0, END)
        self.rados_speed.insert(0, "%d" % (cfg.rados_recover / MiB))
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Space Usage (%)").grid(row=r)
        self.rados_fullness = Spinbox(f, values=self.fullness,
                    width=self.med_wid)
        self.rados_fullness.grid(row=r + 1)
        self.rados_fullness.delete(0, END)
        self.rados_fullness.insert(0, "%d" % (cfg.rados_fullness * 100))
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Declustering (pg)").grid(row=r)
        self.rados_pgs = Entry(f, width=self.med_wid)
        self.rados_pgs.delete(0, END)
        self.rados_pgs.insert(0, self.med_fmt % cfg.rados_decluster)
        self.rados_pgs.grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Stripe Length").grid(row=r)
        self.stripe_length = Entry(f, width=self.med_wid)
        self.stripe_length.delete(0, END)
        self.stripe_length.insert(0, self.med_fmt % cfg.stripe_length)
        self.stripe_length.grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        while r < self.ROWS:
            Label(f).grid(row=r)
            r += 1
        Button(f, text="RELIABILITY", command=self.do_rados).grid(row=r)
        f.grid(column=3, row=1)

        # fourth stack (remote site)
        r = 1
        f = Frame(t, bd=self.BORDER, relief=RIDGE)
        Label(f, text="RADOS Sites").grid(row=r)
        self.site_num = Spinbox(f, values=self.site_count,
            width=self.short_wid)
        self.site_num.grid(row=r + 1)
        self.site_num.delete(0, END)
        self.site_num.insert(0, "%d" % cfg.remote_sites)
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Rep Latency (s)").grid(row=r)
        self.remote_latency = Spinbox(f, values=self.async_latencies,
                    width=self.long_wid)
        self.remote_latency.grid(row=r + 1)
        self.remote_latency.delete(0, END)
        self.remote_latency.insert(0, "%d" % (cfg.remote_latency * 60 * 60))
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Recovery (MiB/s)").grid(row=r)
        self.remote_speed = Spinbox(f, values=self.remote_speeds,
            width=self.med_wid)
        self.remote_speed.grid(row=r + 1)
        self.remote_speed.delete(0, END)
        self.remote_speed.insert(0, "%d" % (cfg.remote_recover / MiB))
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Disaster (years)").grid(row=r)
        self.remote_fail = Spinbox(f, values=self.site_destroy,
            width=self.long_wid)
        self.remote_fail.grid(row=r + 1)
        self.remote_fail.delete(0, END)
        self.remote_fail.insert(0, "1000")
        # FIX - get this from cfg ... but translate from FITS
        Label(f).grid(column=2, row=r + 2)
        r += 3
        Label(f, text="Site Recover (days)").grid(row=r)
        self.remote_avail = Spinbox(f, values=self.site_recover,
            width=self.long_wid)
        self.remote_avail.grid(row=r + 1)
        self.remote_avail.delete(0, END)
        self.remote_avail.insert(0, "30")
        # FIX - get this from cfg ... but translate from FITS
        Label(f).grid(row=r + 2)
        r += 3
        while r < self.ROWS:
            Label(f).grid(row=r)
            r += 1
        Button(f, text="RELIABILITY", command=self.do_sites).grid(row=r)
        f.grid(column=4, row=1)

        # and the control panel
        r = 2
        c = 1
        Label(t).grid(column=c, row=r)
        Label(t, text="NRE model").grid(column=c, row=r + 1)
        self.nre_model = StringVar(t)
        self.nre_model.set(self.cfg.nre_model)
        OptionMenu(t, self.nre_model, *self.nreTypes).grid(column=c,
                                                        row=r + 2)

        c = 2
        Label(t).grid(column=c, row=r)
        Label(t, text="Period (years)").grid(column=c, row=r + 1)
        self.period = Spinbox(t, from_=1, to=10, width=self.short_wid)
        self.period.grid(column=c, row=r + 2)

        c = 3
        Label(t).grid(column=c, row=r)
        Label(t, text="Object size").grid(column=c, row=r + 1)
        # generate object sizes dynamically from parameters
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
            os *= self.step_obj_size
        self.obj_size = Spinbox(t, values=self.object_sizes,
            width=self.long_wid)
        self.obj_size.grid(column=c, row=r + 2)
        self.obj_size.delete(0, END)
        self.obj_size.insert(0, self.object_sizes[0])

        c = 4
        Label(t).grid(column=c, row=r)
        Label(t, text="Verbosity").grid(column=c, row=r + 1)
        self.verbosity = StringVar(t)
        self.verbosity.set(cfg.verbose)
        OptionMenu(t, self.verbosity, *self.verbosities).grid(column=c,
                                                        row=r + 2)

        # and then finalize everything
        t.grid()

    def getCfgInfo(self):
        """ scrape configuration information out of the widgets """
        self.cfg.period = 365.25 * 24 * int(self.period.get())
        self.cfg.disk_type = self.disk_type.get()
        self.cfg.disk_size = int(self.disk_size.get()) * GiB
        self.cfg.disk_nre = float(self.disk_nre.get())
        self.cfg.disk_fit = int(self.disk_fit.get())
        self.cfg.disk_fit2 = int(self.disk_fit2.get())
        self.cfg.raid_vols = int(self.raid_vols.get())
        self.cfg.raid_type = self.raid_type.get()
        self.cfg.raid_replace = int(self.raid_rplc.get())
        self.cfg.raid_recover = int(self.raid_speed.get()) * MiB
        self.cfg.nre_model = self.nre_model.get()
        self.cfg.rados_copies = int(self.rados_cpys.get())
        self.cfg.rados_markout = float(self.rados_down.get()) / 60
        self.cfg.rados_recover = int(self.rados_speed.get()) * MiB
        self.cfg.rados_decluster = int(self.rados_pgs.get())
        self.cfg.stripe_length = int(self.stripe_length.get())
        self.cfg.rados_fullness = float(self.rados_fullness.get()) / 100
        self.cfg.remote_latency = float(self.remote_latency.get()) / (60 * 60)
        self.cfg.remote_sites = int(self.site_num.get())
        self.cfg.remote_recover = int(self.remote_speed.get()) * MiB
        self.cfg.verbose = self.verbosity.get()

        # these parameters can also have the value "never"
        v = self.remote_fail.get()
        self.cfg.majeure = 0 if v == "never" else \
            1000000000 / (float(self.remote_fail.get()) * 365.25 * 24)
        v = self.remote_avail.get()
        self.cfg.site_recover = 0 if v == "never" else \
            float(self.remote_avail.get()) * 24

        # a more complex process for the dynamically generated lists
        self.cfg.obj_size = self.min_obj_size
        i = 0
        while i < len(self.object_sizes) and \
                self.cfg.obj_size < self.max_obj_size:
            if self.obj_size.get() == self.object_sizes[i]:
                break
            self.cfg.obj_size *= self.step_obj_size
            i += 1

        # sanity checking on arguments with limits
        if self.cfg.stripe_length < 1:
            self.cfg.stripe_length = 1
        if self.cfg.stripe_length > self.cfg.rados_decluster:
            print("\nIGNORING stripe width (%d) > decluster (%d)\n" %
                (self.cfg.stripe_length, self.cfg.rados_decluster))
            self.cfg.stripe_length = self.cfg.rados_decluster

    def mainloop(self):
        self.root.mainloop()
