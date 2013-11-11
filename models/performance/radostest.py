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
RADOS simulation exerciser
"""

from Report import Report
from units import *


def radostest(fs, obj_size=16 * MEG, nobj=2500,
              clients=1, depth=1, copies=1, crtdlt=False,
              bsizes=(4096, 128 * 1024, 4096 * 1024)):
    """ compute & display standard filestore test results """

    if crtdlt:
        tc = fs.create(depth=depth)
        td = fs.delete(depth=depth)
        r = Report(("create", "delete"))
        r.printHeading()
        r.printIOPS(1, (SECOND / tc, SECOND / td))
        r.printLatency(1, (tc, td))

    r = Report(("rnd read", "rnd write"))
    r.printHeading()
    for bs in bsizes:
        trr = fs.read(bs, obj_size, nobj=nobj, clients=clients, depth=depth)
        trw = fs.write(bs, obj_size, nobj=nobj, depth=depth,
                       clients=clients, copies=copies)
        # compute the corresponding bandwidths
        brr = bs * SECOND / trr
        brw = bs * SECOND / trw

        r.printBW(bs, (brr, brw))
        r.printIOPS(bs, (brr, brw))
        #r.printLatency(bs, (trr, trw))
