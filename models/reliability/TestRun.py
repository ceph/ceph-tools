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


def printSize(sz):
    """ print out a size with the appropriate unit suffix """

    fmt = ["%dB", "%dKB", "%dMB", "%dGB", "%dTB", "%dPB"]
    i = 0
    while i < len(fmt):
        if sz < 1000:
            break
        sz /= 1000
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


def TestRun(tests, period=RelyFuncts.YEAR, objsize=1 * GB):
    """ run and report a set of specified simulations
        tests -- actual list of simulations to run
        disk -- disk simulation (for parameter reporting)
        raid -- raid simulation (for parameter reporting)
        rados --- rados simulation (for parameter reporting)
        period -- simulation period
        objsize -- size of a single object
    """

    # introspect the tests to find the disk/raid/rados parameters
    raid = None
    rados = None
    site = None
    for t in tests:
        c = t.__class__.__name__
        if raid == None and c.startswith("RAID"):
            raid = t
        if rados == None and c.startswith("RADOS"):
            rados = t
        if site == None and c.startswith("Site"):
            site = t
    disk = rados.disk

    print("")
    print("Disk Modeling Parameters")
    print("    size:     %10s" % printSize(rados.disk.size))
    print("    FIT rate: %10d (%f/year)" %
          (rados.disk.fits, rados.disk.p_failure(period=RelyFuncts.YEAR)))
    print("    NRE rate: %10.1E" % (rados.disk.nre))

    vol_per_pb = PB / rados.disk.size

    print("RAID parameters")
    print("    replace:  %16s" % (printTime(raid.delay)))
    print("    recovery: %10s/s (%s)" %
                (printSize(raid.speed), printTime(raid.rebuild_time())))
    print("    NRE model:%10s" % (raid.nre))

    print("RADOS parameters")
    print("    mark-out:  %16s" % printTime(rados.delay))
    print("    recovery:  %10s/s (%s)" %
                (printSize(rados.speed), printTime(rados.rebuild_time())))
    print("    object size:%9s" % printSize(objsize))

    hfmt = "    %-20s %12s %12s %12s %12s"
    dfmt = "    %-20s %11.6f%% %12.2E %12.2E %12s"

    if site != None:
        print("Number of Sites: %d" % (site.sites))
        if site.fits == 0:
            print("    disasters:  IGNORED")
        else:
            tf = RelyFuncts.BILLION / site.fits
            tr = RelyFuncts.BILLION / site.repair
            print("    disasters:    %12s" % (printTime(tf)))
            print("    replacement:  %12s" % printTime(tr))
            print("    lambda/mu:    %d/%d" % (site.fits, site.repair))
        seconds = (disk.size / site.speed) * RelyFuncts.SECOND
        print("    recovery: %10s/s (%s)" %
            (printSize(site.speed), printTime(seconds)))

    print("")

    print("Expected failures, data loss (per drive/site, per PB) in %s" %
                    (printTime(period)))
    print(hfmt % ("storage", "fail/unit", "bytes/unit",
            "bytes/PB", "durability"))
    print(hfmt % ("-------", "----------", "-----------",
            "--------", "----------"))

    # expected data loss after drive failures
    for t in tests:
        if t == None:
            continue

        # probability of a data loss due to drive failure
        p_fail = t.p_failure(period=period)

        # expected data loss due to such failures
        l_fail = p_fail * t.loss()

        # expected data loss from NREs during recovery
        l_nre = p_fail * t.p_nre() * t.loss_nre(objsize)

        # total expected loss (per drive, and per PB)
        loss_d = l_fail + l_nre
        if t.__class__.__name__ == "Site":
            loss_p = loss_d * PB / t.size
            durability = float(1 - p_fail)
        else:
            loss_p = loss_d * vol_per_pb
            durability = float(1 - p_fail) ** vol_per_pb

        # figure out how to render the durability
        if durability < .999999:
            d = "%6.3f%%" % (durability * 100)
        else:
            nines = 0
            while durability > .9:
                nines += 1
                durability -= .9
                durability *= 10
            d = "%d-nines" % (nines)

        print(dfmt % (t.description, p_fail * 100, loss_d, loss_p, d))
