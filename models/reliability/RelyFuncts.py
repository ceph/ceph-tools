#
# basic mathematical functions used in reliability modeling
#

import math

# units of time (FIT rates)
HOUR = 1
MINUTE = float(HOUR) / 60
SECOND = float(HOUR) / 3600
DAY = float(HOUR * 24)
YEAR = (HOUR * 24 * 365.25)


def failures(fitRate, hours):
    """ expected number of failures in an interval """
    return float(fitRate) * hours / 1000000000


def Pn(fitRate, hours, n=1):
    """ probability of exactly n failures during an interval """
    fails = failures(fitRate, hours)
    p = math.exp(-fails)
    if n > 0:
        p *= (fails ** n)
        p /= math.factorial(n)
    return p
