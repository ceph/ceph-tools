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


def FitRate(events, period=YEAR):
    """ return the FIT rate corresponding to a rate in other unit"""
    return events * 1000000000 / period


def mttf(fits):
    """ return the MTTF corresponding to an FIT rate """
    return 1000000000 / fits


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
