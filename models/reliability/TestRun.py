#
# run a series of tests
#
#   This is the module that knows how to run a simulation, and
#   how to report the results.
#

import RelyFuncts
import DiskRely
import RaidRely
import RadosRely


# handy storage units
KB = 1000
MB = KB * 1000
GB = MB * 1000
TB = GB * 1000
PB = TB * 1000


def printSize(sz, unit=1000):
    """ print out a size with the appropriate unit suffix """

    fmt = ["%dB", "%dKB", "%dMB", "%dGB", "%dTB", "%dPB"]
    i = 0
    while i < len(fmt):
        if sz < unit:
            break
        sz /= unit
        i += 1
    return fmt[i] % (sz)


def printTime(t):
    """ print out a time in an appropriate unit """
    if t < 2 * RelyFuncts.MINUTE:
        return "%d seconds" % (t / RelyFuncts.SECOND)
    if t < 5 * RelyFuncts.HOUR:
        return "%d minutes" % (t / RelyFuncts.MINUTE)
    if t < 3 * RelyFuncts.DAY:
        return "%d hours" % (t / RelyFuncts.HOUR)
    if t < RelyFuncts.YEAR:
        return "%d days" % (t / RelyFuncts.DAY)
    if (t % RelyFuncts.YEAR) == 0:
        return "%d years" % (t / RelyFuncts.YEAR)
    else:
        return "%5.1f years" % (t / RelyFuncts.YEAR)


def TestRun(tests, period=RelyFuncts.YEAR,
            objsize=1 * GB, stripe=4 * MB,
            parms=True, headings=True):
    """ run and report a set of specified simulations
        tests -- actual list of simulations to run
                (print a header line for each None test)
        period -- simulation period
        objsize -- size of a single object
        stripe -- width for striped objects
        parms -- print out general simulation parameters
        heads -- print out column headings
    """

    # output formats
    hfmt = "    %-20s %12s %12s %12s %12s"
    dfmt = "    %-20s %12s %12.2E %12.2E %12s"
    lines = ("-------", "----------", "-----------", "--------", "----------")
    heads = ("storage", "fail/unit", "bytes/unit", "bytes/PB", "durability")

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
        print("Disk Modeling Parameters")
        print("    size:     %10s" % printSize(disk.size))
        print("    FIT rate: %10d (%f/year)" %
              (disk.fits, disk.p_failure(period=RelyFuncts.YEAR)))
        print("    NRE rate: %10.1E" % (disk.nre))

    if parms and raid is not None:
        print("RAID parameters")
        print("    replace:  %16s" % (printTime(raid.delay)))
        print("    recovery rate: %7s/s (%s)" %
                    (printSize(raid.speed), printTime(raid.rebuild_time())))
        print("    NRE model:        %10s" % (raid.nre))

    if parms and rados is not None:
        print("RADOS parameters")
        print("    auto mark-out: %14s" % printTime(rados.delay))
        print("    recovery rate: %8s/s (%s)" %
                    (printSize(rados.speed), printTime(rados.rebuild_time())))
        print("    osd fullness: %7d%%" % (rados.full * 100))
        print("    declustering: %7d PG/OSD" % (rados.pgs))
        print("    NRE model:        %10s" % (rados.nre))
        print("    object size:  %7s" % printSize(objsize, unit=1024))
        print("    stripe width: %7s" %
            ("NONE" if stripe == 0 else printSize(stripe, unit=1024)))

    if parms and site is not None:
        print("Site parameters")
        s = 0 if multi is None else multi.sites
        if site.fits == 0:
            print("    disasters:    IGNORED")
        else:
            tf = RelyFuncts.BILLION / site.fits
            print("    disaster rate: %12s (%d FITS)" %
                (printTime(tf), site.fits))
        if site.replace == 0:
            print("    site recovery:   NEVER")
        else:
            print("    site recovery: %11s" %
                    (printTime(site.replace)))

        if multi is not None:
            print("    recovery rate: %8s/s (%s)" %
                (printSize(multi.speed), printTime(multi.recovery)))
            if multi.latency == 0:
                print("    replication:       synchronous")
            else:
                print("    replication:       asynchronous (%s delay)" %
                            (printTime(multi.latency)))

    if parms:
        print("")
        print("Expected failures, data loss (per drive/site, per PB) in %s" %
                (printTime(period)))

    if headings:
        print("")
        print(hfmt % heads)
        print(hfmt % lines)

    # expected data loss after drive failures
    for t in tests:
        if t is None:
            print("")
            print(hfmt % heads)
            print(hfmt % lines)
            continue

        # probability of a data loss due to drive failure
        p_fail = t.p_failure(period=period)
        if p_fail > .0000001:
            p = "%11.6f%%" % (p_fail * 100)
        else:
            p = "%12.3e" % (p_fail)

        # expected data loss due to such failures
        l_fail = p_fail * t.loss()

        # expected data loss from NREs during recovery
        l_nre = p_fail * t.p_nre() * t.loss_nre(objsize)

        # total expected loss (per drive, and per PB)
        loss_d = l_fail + l_nre
        if t.__class__.__name__ == "Site":
            loss_p = loss_d * PB / t.size
            durability = float(1 - p_fail)
        elif t.__class__.__name__ == "MultiSite":
            loss_p = loss_d * PB / t.site.size
            durability = float(1 - p_fail)
        else:
            vol_per_pb = PB / disk.size
            loss_p = loss_d * vol_per_pb
            durability = float(1 - p_fail) ** vol_per_pb

        # figure out how to render the durability
        if durability < .99999:
            d = "%6.3f%%" % (durability * 100)
        else:
            nines = 0
            while durability > .9:
                nines += 1
                durability -= .9
                durability *= 10
            d = "%d-nines" % (nines)

        print(dfmt % (t.description, p, loss_d, loss_p, d))
