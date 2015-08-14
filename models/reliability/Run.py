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

from ColumnPrint import ColumnPrint
from RelyFuncts import mttf, YEAR
from sizes import PiB

"""
run a series of tests
   This is the module that knows how to run a simulation,
   and how to report the results.
"""


def printParms(fmt, disk, raid, rados, site, multi):
    """
        print out the parameters associated with a test
    """
    if disk is not None:
        print "Disk Modeling Parameters"
        print "    size:     %10s" % fmt.printSize(disk.size)
        print("    FIT rate: %10d (MTBF = %s)" %
              (disk.fits, fmt.printTime(mttf(disk.fits))))
        print "    NRE rate: %10.1E" % disk.nre

    if raid is not None:
        print "RAID parameters"
        print "    replace:  %16s" % fmt.printTime(raid.delay)
        if raid.speed > 0:
            print("    recovery rate: %7s/s (%s)" %
                  (fmt.printSize(raid.speed),
                   fmt.printTime(raid.rebuild_time())))
        print "    NRE model:        %10s" % raid.nre_model
        print "    object size:      %10s" % fmt.printSize(raid.objsize)

    if rados is not None:
        print "RADOS parameters"
        print "    auto mark-out: %14s" % fmt.printTime(rados.delay)
        print("    recovery rate: %8s/s (%s/drive)" %
              (fmt.printSize(rados.speed),

               fmt.printTime(rados.rebuild_time(rados.speed))))
        print "    osd fullness: %7d%%" % (rados.full * 100)
        print "    declustering: %7d PG/OSD" % rados.pgs
        print "    NRE model:        %10s" % rados.nre_model
        print "    object size:  %7s" % \
              fmt.printSize(rados.objsize, unit=1024)
        print "    stripe length:%7d" % rados.stripe

    if site is not None:
        print "Site parameters"
        s = 0 if multi is None else multi.sites
        if site.fits == 0:
            print "    disasters:    IGNORED"
        else:
            tf = mttf(site.fits)
            print("    disaster rate: %12s (%d FITS)" %
                  (fmt.printTime(tf), site.fits))
        if site.replace == 0:
            print "    site recovery:   NEVER"
        else:
            print "    site recovery: %11s" % fmt.printTime(site.replace)

        if multi is not None:
            print("    recovery rate: %8s/s (%s/PG)" %
                  (fmt.printSize(multi.speed),
                   fmt.printTime(multi.rados.rebuild_time(multi.speed))))
            if multi.latency == 0:
                print "    replication:       synchronous"
            else:
                print("    replication:       asynchronous (%s delay)" %
                      (fmt.printTime(multi.latency)))


def Run(tests, period=YEAR, verbosity="all"):
    """ run and report a set of specified simulations
        tests -- actual list of simulations to run
                (print a header line for each None test)
        period -- simulation period
        verbosity -- output options
    """

    # column headings
    heads = ("storage", "durability",
             "PL(site)", "PL(copies)", "PL(NRE)", "PL(rep)", "loss/PiB")

    # column descriptions
    legends = [
        "storage unit/configuration being modeled",
        "probability of object survival*",
        "probability of loss due to site failures*",
        "probability of loss due to drive failures*",
        "probability of loss due to NREs during recovery*",
        "probability of loss due to replication failure*",
        "expected data loss per Petabyte*"
    ]

    # use the headings to generate a format
    format = ColumnPrint(heads, maxdesc=20)

    # figure out what output he wants
    headings = True
    parms = True
    descr = True
    if verbosity == "parameters":
        descr = False
    elif verbosity == "headings":
        parms = False
        descr = False
    elif verbosity == "data only":
        parms = False
        descr = False
        headings = False

    # introspect the tests to find the disk/raid/rados parameters
    disk = None
    raid = None
    rados = None
    site = None
    multi = None
    for t in tests:
        c = t.__class__.__name__
        if disk is None and "Disk" in c:
            disk = t
        if raid is None and c.startswith("RAID"):
            raid = t
        if rados is None and c.startswith("RADOS"):
            rados = t
        if site is None and c.startswith("Site"):
            site = t
        if multi is None and c.startswith("MultiSite"):
            multi = t

    # find elements that only exist beneath others
    if site is None and multi is not None:
        site = multi.site
    if rados is None and multi is not None:
        rados = multi.rados
    if disk is None and rados is not None:
        disk = rados.disk
    if disk is None and raid is not None:
        disk = raid.disk

    if parms:
        printParms(format, disk, raid, rados, site, multi)

    if descr:
        print ""
        print "Column legends"
        s = format.printTime(period)
        i = 1
        while i <= len(legends):
            l = legends[i - 1]
            if l.endswith('*'):
                print "\t%d %s (per %s)" % (i, l, s)
            else:
                print "\t%d %s" % (i, l)
            i += 1

    if headings:
        format.printHeadings()

    # expected data loss after drive failures
    for t in tests:
        if t is None:
            format.printHeadings()
            continue

        # calculate the renderable reliabilities and durability
        s = list()
        t.compute(period=period)
        s.append(t.description)                 # description
        s.append(format.printDurability(t.dur))        # durability
        s.append(format.printProbability(t.P_site))    # P(site failure)
        s.append(format.printProbability(t.P_drive))   # P(drive failure)
        s.append(format.printProbability(t.P_nre))     # P(NRE on recovery)
        s.append(format.printProbability(t.P_rep))     # P(replication failure)
        l = (t.P_site * t.L_site) + (t.P_drive * t.L_drive) +\
            (t.P_nre * t.L_nre) + (t.P_rep * t.L_rep)
        s.append(format.printFloat(l * PiB / t.rawsize))   # expected loss/PiB
        format.printLine(s)
