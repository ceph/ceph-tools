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
run a series of tests
   This is the module that knows how to run a simulation,
   and how to report the results.
"""

from RelyFuncts import SECOND, MINUTE, HOUR, DAY, YEAR, mttf
from sizes import KiB, MiB, GiB, TiB, PiB


def getFormat(headings):
    """ derive the format string """
    Indent = 4
    DescWid = 20
    ColWid = 12

    # figure out how wide our columns have to be
    wid = 0
    for s in headings:
        if len(s) > wid:
            wid = len(s)
    if wid >= ColWid:
        ColWid = wid + 1

    # generate the format string
    f = ""
    i = 0
    while i < Indent:
        f += ' '
        i += 1

    col = 0
    while col < len(headings):
        wid = DescWid if col == 0 else ColWid
        f += '%'
        if col == 0:
            f += "-%ds" % wid
        else:
            f += "%ds" % wid
        col += 1
    return f


def printHeadings(headings, format):
    """ print out a set of column headings """
    print ""
    print format % headings

    # how wide should a dash be
    dashes = 0
    for s in headings:
        if len(s) > dashes:
            dashes = len(s)

    # create a line with that many dashes
    s = ""
    while dashes > 0:
        s += '-'
        dashes -= 1

    # create a tupple with the right number of lines
    l = list()
    i = 0
    while i < len(headings):
        l.append(s)
        i += 1

    print format % tuple(l)


def printSize(sz, unit=1000):
    """ print out a size with the appropriate unit suffix """

    fmt10 = ["%dB", "%dKiB", "%dMiB", "%dGiB", "%dTiB", "%dPiB"]
    fmt2 = ["%dB", "%dKB", "%dMB", "%dGB", "%dTB", "%dPB"]
    fmt = fmt10 if unit == 1000 else fmt2
    i = 0
    while i < len(fmt):
        if sz < unit:
            break
        sz /= unit
        i += 1
    return fmt[i] % (sz)


def printTime(t):
    """ print out a time in an appropriate unit """
    if t < 2 * MINUTE:
        return "%d seconds" % (t / SECOND)
    if t < 5 * HOUR:
        return "%d minutes" % (t / MINUTE)
    if t < 3 * DAY:
        return "%d hours" % (t / HOUR)
    if t < YEAR:
        return "%d days" % (t / DAY)
    if (t % YEAR) == 0:
        return "%d years" % (t / YEAR)
    else:
        return "%5.1f years" % (t / YEAR)


def printDurability(d):
    """ print out a durability in a reasonable format """
    if d < .99999:
        return "%6.3f%%" % (d * 100)
    else:
        nines = 0
        while d > .9:
            nines += 1
            d -= .9
            d *= 10
        return "%d-nines" % (nines)


def printProbability(p):
    """ print out a probability in a reasonable format """
    if p > .0000001:
        return "%9.6f%%" % (p * 100)
    else:
        return "%9.3e" % (p)


def printFloat(f):
    return "%9.3e" % (f)


def Run(tests, period=YEAR, verbosity="all"):
    """ run and report a set of specified simulations
        tests -- actual list of simulations to run
                (print a header line for each None test)
        period -- simulation period
        verbosity -- output options
    """

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

    if parms and disk is not None:
        print "Disk Modeling Parameters"
        print "    size:     %10s" % printSize(disk.size)
        print("    FIT rate: %10d (MTBF = %s)" %
              (disk.fits, printTime(mttf(disk.fits))))
        print "    NRE rate: %10.1E" % disk.nre

    if parms and raid is not None:
        print "RAID parameters"
        print "    replace:  %16s" % printTime(raid.delay)
        if raid.speed > 0:
            print("    recovery rate: %7s/s (%s)" %
                  (printSize(raid.speed),
                   printTime(raid.rebuild_time())))
        print "    NRE model:        %10s" % raid.nre_model
        print "    object size:      %10s" % printSize(raid.objsize)

    if parms and rados is not None:
        print "RADOS parameters"
        print "    auto mark-out: %14s" % printTime(rados.delay)
        print("    recovery rate: %8s/s (%s/drive)" %
              (printSize(rados.speed),
               printTime(rados.rebuild_time(rados.speed))))
        print "    osd fullness: %7d%%" % (rados.full * 100)
        print "    declustering: %7d PG/OSD" % rados.pgs
        print "    NRE model:        %10s" % rados.nre_model
        print "    object size:  %7s" % printSize(rados.objsize, unit=1024)
        print "    stripe length:%7d" % rados.stripe

    if parms and site is not None:
        print "Site parameters"
        s = 0 if multi is None else multi.sites
        if site.fits == 0:
            print "    disasters:    IGNORED"
        else:
            tf = mttf(site.fits)
            print("    disaster rate: %12s (%d FITS)" %
                  (printTime(tf), site.fits))
        if site.replace == 0:
            print "    site recovery:   NEVER"
        else:
            print "    site recovery: %11s" % printTime(site.replace)

        if multi is not None:
            print("    recovery rate: %8s/s (%s/PG)" %
                  (printSize(multi.speed),
                   printTime(multi.rados.rebuild_time(multi.speed))))
            if multi.latency == 0:
                print "    replication:       synchronous"
            else:
                print("    replication:       asynchronous (%s delay)" %
                      (printTime(multi.latency)))

    # column headings
    heads = ("storage", "durability",
             "PL(site)", "PL(copies)", "PL(NRE)", "PL(rep)", "loss/PiB")
    format = getFormat(heads)

    # column descriptions
    legends = [
        "storage unit/configuration being modeled",
        "probability of object survival",
        "probability of loss due to site failures",
        "probability of loss due to drive failures",
        "probability of loss due to NREs during recovery",
        "probability of loss due to replication failure",
        "expected data loss per Petabyte"
    ]

    if descr:
        print ""
        print "Column legends"
        s = printTime(period)
        i = 1
        while i <= len(legends):
            l = legends[i - 1]
            if i == 1:
                print "\t%d %s" % (i, l)
            else:
                print "\t%d %s (per %s)" % (i, l, s)
            i += 1

    if headings:
        printHeadings(heads, format)

    # expected data loss after drive failures
    for t in tests:
        if t is None:
            printHeadings(heads, format)
            continue

        # calculate the renderable reliabilities and durability
        s = list()
        t.compute(period=period)
        s.append(t.description)                 # description
        s.append(printDurability(t.dur))        # durability
        s.append(printProbability(t.P_site))    # P(site failure)
        s.append(printProbability(t.P_drive))   # P(drive failure)
        s.append(printProbability(t.P_nre))     # P(NRE on recovery)
        s.append(printProbability(t.P_rep))     # P(replication failure)
        l = (t.P_site * t.L_site) + (t.P_drive * t.L_drive) +\
            (t.P_nre * t.L_nre) + (t.P_rep * t.L_rep)
        s.append(printFloat(l * PiB / t.rawsize))   # expected data loss/PiB
        print format % tuple(s)
