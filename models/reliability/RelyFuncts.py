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
basic mathematical functions used in reliability modeling

   for some reason I felt inclined not to ask clients to know what the
   denominator for FIT rates was, so I have provided routines to
   convert between FITs and convenient units
"""

import math

# units of time (FIT rates)
HOUR = 1
MINUTE = float(HOUR) / 60
SECOND = float(HOUR) / 3600
DAY = float(HOUR * 24)
YEAR = (HOUR * 24 * 365.25)

BILLION = 1000000000


def FitRate(events, period=YEAR):
    """ FIT rate corresponding to a rate in other unit
            events -- number of events
            period --  period in which that many events happen
    """
    return events * BILLION / period


def mttf(fits):
    """ MTTF corresponding to an FIT rate
            fits --- FIT rate
    """
    return BILLION / fits


def Pfail(fitRate, hours, n=1):
    """ probability of exactly n failures during an interval
            fitRate -- nominal FIT rate
            hours -- number of hours to await event
            n -- number of events for which we want estimate
    """

    expected = float(fitRate) * hours / 1000000000
    p = math.exp(-expected)
    if n > 0:
        p *= (expected ** n)
        p /= math.factorial(n)
    return p


def Pn(expected=1, n=0):
    """ probability of n events occurring when exp are expected
            exp -- number of events expected during this period
            n -- number of events for which we want estimate
    """
    p = math.exp(-expected)
    if n > 0:
        p *= (expected ** n)
        p /= math.factorial(n)
    return p


def multiFit(fitRate, total, required, repair, oneRepair=True):
    """ effective FIT rate required/total redundant components
            fitRate -- FIT rate of a single component
            total -- number of redundant components in system
            required -- number required for continued operation
            repair -- repair time (in hours)
            oneRepair -- all failures within a single repair period

        FITs(all_fail) =
            FITs(initial failure) * P(rest fail during repair period)
    """

    # FIX ... these are only approximations, I should do better
    fits = total * fitRate      # initial FIT rate
    total -= 1                  # we are down one
    if oneRepair:
        # all failures must occur within a single repair period
        # note: this very slightly under-estimates P_restfail in cases
        #       where required > 1
        P_restfail = Pfail(total*fitRate, repair, n=total+1-required)
        fits *= P_restfail
    else:
        # each failure starts a new repair period
        # note: these numbers are small enough that expected reasonably
        #       approximates the probability
        while total >= required:
            P_nextfail = total * fitRate * repair * 10E-9
            fits *= P_nextfail
            total -= 1
    return fits
