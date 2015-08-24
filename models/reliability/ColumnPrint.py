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
#
# This is a class to output model results (times, capacities, durabilities,
# and probabilities) in attractive, standard width columns.
#
#   This class defines a standard string format for each line.
#   It includes methods to turn many data types into strings.
#   Create each output line as a vector of string (values),
#   and then print it with the chosen format.
#

from RelyFuncts import YEAR, DAY, HOUR, MINUTE, SECOND


class ColumnPrint:
    """ a class to produce attractive columnar output """

    def __init__(self, headings, maxdesc=20):
        """ derive the format string """
        self.headings = headings
        Indent = 4
        DescWid = maxdesc
        ColWid = 12

        # figure out how wide our columns have to be
        wid = 0
        for s in self.headings:
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
        while col < len(self.headings):
            wid = DescWid if col == 0 else ColWid
            f += '%'
            if col == 0:
                f += "-%ds" % wid
            else:
                f += "%ds" % wid
            col += 1

        self.format = f

    def printLine(self, list):
        """ print an output line from a list (of string items) """
        print(self.format % tuple(list))

    def printHeadings(self):
        """ print out a set of column headings and separator line """
        print ""
        print self.format % self.headings

        # how wide should a dash be
        dashes = 0
        for s in self.headings:
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
        while i < len(self.headings):
            l.append(s)
            i += 1

        print self.format % tuple(l)

    def printSize(self, sz, unit=1000):
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

    def printTime(self, t):
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

    def printDurability(self, d):
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

    def printProbability(self, p):
        """ print out a probability in a reasonable format """
        if p > .0000001:
            return "%9.6f%%" % (p * 100)
        else:
            return "%9.3e" % (p)

    def printFloat(self, f):
        return "%9.3e" % (f)
