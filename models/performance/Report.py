#!/usr/bin/python
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
nicely formatted output for multi-column bandwidth, iops and latency reports
"""

from units import *


class Report:

    def __init__(self, headings):
        """
            instantiate a throughput/IOPS report
            headings --- array of data column headings
        """

        # default layout parameters
        data_width = 7
        data_units = 4
        column_sep = 3
        line_width = 5
        extra = 0

        # first column is alwasys block size
        headings = ("size",) + headings

        # make sure our lines are wide enough
        for h in headings:
            l = len(h)
            if (l > data_width + data_units + 1 + extra):
                extra = l - (data_width + data_units + 1)
            if (l > line_width):
                line_width = l

        line = line_width * "-"
        lines = ()

        # create our format lines
        self.h_fmt = ""
        for h in headings:
            self.h_fmt += column_sep * " "
            self.h_fmt += "%%%ds" % (data_width + data_units + 1)
            lines += (line,)

        self.h_string = self.h_fmt % headings
        self.h_lines = self.h_fmt % lines

    def printHeading(self):
        """ print out column headings and dividing lines """
        print self.h_string
        print self.h_lines

    def printBW(self, bs, vector):
        """ print out a bandwidth report
            bs -- block size
            vector -- B/s bw values for each column
        """

        # start with the block size
        if (bs >= MB):
            tp = ("%dM" % (bs / MB),)
        else:
            tp = ("%dK" % (bs / KB),)

        for bw in vector:
            if bw >= 100 * MB:
                tp += ("%7d MB/s" % ((bw + 500000) / MEG),)
            elif bw < 10 * MB:
                tp += ("%7.2f MB/s" % (float(bw + 5000) / MEG),)
            else:
                tp += ("%7.1f MB/s" % (float(bw + 50000) / MEG),)
        print(self.h_fmt % tp)

    def printIOPS(self, bs, vector):
        """ print out an IOPS report
            bs -- block size
            vector -- B/s bw values for each column
        """

        iops = ("",)
        for bw in vector:
            iops += ("%7d IOPS" % (bw / bs),)
        print(self.h_fmt % iops)

    def printLatency(self, bs, vector):
        """ print out a latency report
            bs -- block size
            vector -- us latency values for each column
        """

        lat = ("",)
        for l in vector:
            lat += ("%7d us  " % (l),)
        print(self.h_fmt % lat)
