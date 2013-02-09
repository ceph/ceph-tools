#!/USR/BIn/python
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
        0, 1, 5, 10, 30, 60, 300, 600, 900, 1800, 3600,
        2 * 3600, 6 * 3600, 12 * 3600, 18 * 3600, 24 * 3600
    ]

    fullness = [    # list of likely volume fullness percentages
        50, 75, 80, 85, 90, 95, 100
    ]

    site_count = [  # list of likely remote site numbers
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    ]

    remote_speeds = [   # list of likely remote recovery speeds (MB/s)
        1,  2, 5, 10, 20, 25, 40, 50, 60, 80, 100, 150,
        200, 300, 400, 500, 600, 800, 1000
    ]

    site_destroy = [    # force majeure event frequency
        10, 100, 1000, 10000, 100000, "never"
    ]

    site_recover = [    # number of days to recover a destroyed facility
        1, 2, 4, 8, 12, 16, 20, 30, 40, 50, 60, 80,
        100, 150, 200, 250, 300, 365, "never"
    ]

    yes_no = [
        "no", "yes"
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
    parameters = None
    headers = None

    ROWS = 20
    BORDER = 5

    def __init__(self, cfg, do_disk, do_raid, do_rados, do_sites):
        """ create a GUI panel
            cfg -- default parameter values
            do_parms -- call back for parms button
            do_disk -- call back for disk button
            do_raid -- call back for raid button
            do_rados -- call back for rados button
            do_sites -- call back for sites button
            """

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
        OptionMenu(f, self.disk_type, *self.diskTypes, \
                    command=self.diskchoice).grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="disk FITs").grid(row=r)
        self.disk_fit = Entry(f, width=self.long_wid)
        self.disk_fit.delete(0, END)
        self.disk_fit.insert(0, self.fit_rates[0])
        self.disk_fit.grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="NRE rate").grid(row=r)
        self.disk_nre = Spinbox(f, width=self.long_wid, values=self.nre_rates)
        self.disk_nre.grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Size (GB)").grid(row=r)
        self.disk_size = Entry(f, width=self.long_wid)
        self.disk_size.delete(0, END)
        self.disk_size.insert(0, self.long_fmt % (cfg.disk_size / GB))
        self.disk_size.grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        while r < self.ROWS:
            Label(f).grid(row=r)
            r += 1
        Button(f, text="RELIABILITY", command=do_disk).grid(row=r)
        f.grid(column=1, row=1)

        # second stack (RAID)
        f = Frame(t, bd=self.BORDER, relief=RIDGE)
        r = 1
        Label(f, text="RAID Type").grid(row=r)
        self.raid_type = StringVar(f)
        self.raid_type.set(self.raidTypes[0])
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
        Label(f, text="Rebuild (MB/s)").grid(row=r)
        self.raid_speed = Spinbox(f, width=self.med_wid,
                    values=self.rebuild_speeds)
        self.raid_speed.grid(row=r + 1)
        self.raid_speed.delete(0, END)
        self.raid_speed.insert(0, "%d" % (cfg.raid_recover / MB))
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Volumes").grid(row=r)
        self.raid_vols = Spinbox(f, from_=2, to=10, width=self.short_wid)
        self.raid_vols.grid(row=r + 1)
        Label(f).grid(row=r + 2)
        r += 3
        while r < self.ROWS:
            Label(f).grid(row=r)
            r += 1
        Button(f, text="RELIABILITY", command=do_raid).grid(row=r)
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
        Label(f, text="Recovery (MB/s)").grid(row=r)
        self.rados_speed = Spinbox(f, width=self.med_wid,
                    values=self.rebuild_speeds)
        self.rados_speed.grid(row=r + 1)
        self.rados_speed.delete(0, END)
        self.rados_speed.insert(0, "%d" % (cfg.rados_recover / MB))
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
        Label(f, text="Object size").grid(row=r)
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
        self.obj_size = Spinbox(f, values=self.object_sizes,
            width=self.long_wid)
        self.obj_size.grid(row=r + 1)
        self.obj_size.delete(0, END)
        self.obj_size.insert(0, self.object_sizes[0])
        Label(f).grid(row=r + 2)
        r += 3
        while r < self.ROWS:
            Label(f).grid(row=r)
            r += 1
        Button(f, text="RELIABILITY", command=do_rados).grid(row=r)
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
        Label(f, text="Recovery (MB/s)").grid(row=r)
        self.remote_speed = Spinbox(f, values=self.remote_speeds,
            width=self.med_wid)
        self.remote_speed.grid(row=r + 1)
        self.remote_speed.delete(0, END)
        self.remote_speed.insert(0, "%d" % (cfg.remote_recover / MB))
        Label(f).grid(row=r + 2)
        r += 3
        Label(f, text="Disaster (years)").grid(row=r)
        self.remote_fail = Spinbox(f, values=self.site_destroy,
            width=self.long_wid)
        self.remote_fail.grid(row=r + 1)
        self.remote_fail.delete(0, END)
        self.remote_fail.insert(0, "never")
        Label(f).grid(column=2, row=r + 2)
        r += 3
        Label(f, text="Site Recover (days)").grid(row=r)
        self.remote_avail = Spinbox(f, values=self.site_recover,
            width=self.long_wid)
        self.remote_avail.grid(row=r + 1)
        self.remote_avail.delete(0, END)
        self.remote_avail.insert(0, "never")
        Label(f).grid(row=r + 2)
        r += 3
        while r < self.ROWS:
            Label(f).grid(row=r)
            r += 1
        Button(f, text="RELIABILITY", command=do_sites).grid(row=r)
        f.grid(column=4, row=1)

        # and the control panel
        Label(t).grid(column=1, row=2)
        Label(t, text="NRE model").grid(column=1, row=3)
        self.nre_meaning = StringVar(t)
        self.nre_meaning.set(self.nreTypes[0])
        OptionMenu(t, self.nre_meaning, *self.nreTypes).grid(column=1, row=4)

        Label(t).grid(column=2, row=2)
        Label(t, text="Parameters").grid(column=2, row=3)
        self.parameters = StringVar(t)
        self.parameters.set(self.yes_no[cfg.parms])
        OptionMenu(t, self.parameters, *self.yes_no).grid(column=2, row=4)

        Label(t).grid(column=3, row=2)
        Label(t, text="Headings").grid(column=3, row=3)
        self.headings = StringVar(t)
        self.headings.set(self.yes_no[cfg.headings])
        OptionMenu(t, self.headings, *self.yes_no).grid(column=3, row=4)

        Label(t).grid(column=4, row=2)
        Label(t, text="Period (years)").grid(column=4, row=3)
        self.period = Spinbox(t, from_=1, to=10, width=self.short_wid)
        self.period.grid(row=4, column=4)

        # and then finalize everything
        t.grid()

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
        # cfg.node_fit = int(self.node_fit.get())
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
        cfg.remote_latency = float(self.remote_latency.get()) / (60 * 60)
        cfg.remote_sites = int(self.site_num.get())
        cfg.remote_recover = int(self.remote_speed.get()) * MB
        cfg.parms = 1 if self.parameters.get() == "yes" else 0
        cfg.headings = 1 if self.headings.get() == "yes" else 0

        # these two parameters can also have the value "never"
        v = self.remote_fail.get()
        cfg.majeure = 0 if v == "never" else \
            float(self.remote_fail.get()) * 365.25 * 24
        v = self.remote_avail.get()
        cfg.site_recover = 0 if v == "never" else \
            float(self.remote_avail.get()) * 24

        # a more complex process due to the selection format
        cfg.obj_size = self.min_obj_size
        i = 0
        while i < len(self.object_sizes) and cfg.obj_size < self.max_obj_size:
            if self.obj_size.get() == self.object_sizes[i]:
                break
            cfg.obj_size *= 10
            i += 1

    def mainloop(self):
        self.root.mainloop()
