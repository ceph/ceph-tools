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
K = 1000
M = K * 1000
G = M * 1000
T = G * 1000
P = T * 1000


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
            parms=True, headings=True):
    """ run and report a set of specified simulations
        tests -- actual list of simulations to run
                (print a header line for each None test)
        period -- simulation period
        parms -- print out general simulation parameters
        heads -- print out column headings
    """

    # output formats
    hfmt = "    %-20s %12s %12s %12s %12s"
    dfmt = "    %-20s %12s %12.2E %12.2E %12s"
    lines = ("-------", "---------", "----------", "--------", "----------")
    heads = ("storage", "fail/unit", " loss/unit", " loss/PB", "durability")

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
        print("    object size:  %7s" % printSize(rados.objsize, unit=1024))
        print("    stripe width: %7s" %
            ("NONE" if rados.stripe == 0 \
                    else printSize(rados.stripe, unit=1024)))

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
        s = printTime(period)
        print("")
        print("Column legend")
        print("\t1. storage configuration being modeled")
        print("\t2. probability of unit (drive/group/PG) failure per %s" % (s))
        print("\t3. expected lost bytes (per unit) per %s" % (s))
        print("\t4. expected lost bytes (per PB) per %s" % (s))
        print("\t5. P(no damage/loss) for an arbitrary object in %s" % (s))

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
        l_fail = p_fail * t.loss(period=period)

        # expected data loss from NREs during recovery
        l_nre = p_fail * t.p_nre() * t.loss_nre()

        # total expected loss (per drive, and per PB)
        loss_d = l_fail + l_nre
        loss_p = p_fail * t.loss(period=period, per=P)
        # FIX this does not include NRE losses

        # figure out and render the durability
        durability = t.durability(period=period)
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
