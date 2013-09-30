#!/usr/bin/python
#
# NO COPYRIGHT/COPYLEFT
#
#   This module merely invokes a simulation and displays
#   the results using standard reporting functions.  As it
#   merely uses those API's it is an "application" under the
#   Gnu Lesser General Public Licence.  It can be reproduced,
#   modified, and distributed without restriction.
#

"""
filestore simulation exerciser
"""

from Report import Report
from units import *


def fstoretest(fs, obj_size=4 * MEG, nobj=2500, depth=1, crtdlt=False):
    """ compute & display standard filestore test results """

    if crtdlt:
        tc = fs.create()
        td = fs.delete()

        r = Report(("create", "delete"))
        r.printHeading()
        r.printIOPS(1, (SECOND / tc, SECOND / td))
        r.printLatency(1, (tc, td))

    r = Report(("rnd read", "rnd write"))
    r.printHeading()
    for bs in (4096, 128 * 1024, 4096 * 1024):
        trr = fs.read(bs, obj_size, depth=1, nobj=nobj)
        trw = fs.write(bs, obj_size, depth=depth, nobj=nobj)

        # compute the corresponding bandwidths
        brr = bs * SECOND / trr
        brw = bs * SECOND / trw

        r.printBW(bs, (brr, brw))
        r.printIOPS(bs, (brr, brw))
        #r.printLatency(bs, (trr, trw))
