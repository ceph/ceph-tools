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
        self.data_width = data_width

    def printHeading(self):
        """ print out column headings and dividing lines """
        print(self.h_string)
        print(self.h_lines)

    def getBS(self, bytes):
        """ return an attractively formatted block size """
        if (bytes >= MB):
            return "%dM" % (bytes / MB)
        elif (bytes >= KB):
            return "%dK" % (bytes / KB)
        elif (bytes > 1):
            return "%d" % (bytes)

        # bs <=1 means print nothing
        return ""

    def printBW(self, bs, vector):
        """ print out a bandwidth report
            bs -- block size
            vector -- B/s bw values for each column
        """
        # start with the block size
        tp = (self.getBS(bs),)

        # then add in all the b/w columns
        for bw in vector:
            """ figure out the most appropriate precision """
            if bw >= 100 * MB:
                d_fmt = "%" + "%d" % self.data_width + "d MB/s"
                mb = (bw + 500000) / MEG
            elif bw < 10 * MB:
                d_fmt = "%" + "%d" % self.data_width + ".2f MB/s"
                mb = (bw + 5000) / MEG
            else:
                d_fmt = "%" + "%d" % self.data_width + ".1f MB/s"
                mb = (bw + 50000) / MEG
            tp += (d_fmt % mb,)
        print(self.h_fmt % tp)

    def printIOPS(self, bs, vector):
        """ print out an IOPS report
            bs -- block size
            vector -- B/s bw values for each column
        """

        iops = (self.getBS(bs),)
        d_fmt = "%" + "%d" % self.data_width + "d IOPS"
        for i in vector:
            iops += (d_fmt % i,)
        print(self.h_fmt % iops)

    def printLatency(self, bs, vector):
        """ print out a latency report
            bs -- block size
            vector -- us latency values for each column
        """
        # start with the block size
        lat = (self.getBS(bs),)

        for l in vector:
            """ figure out the most appropriate precision """
            if (l >= 10):
                d_fmt = "%" + "%d" % self.data_width + "d us  "
                lat += (d_fmt % l,)
            elif l < 2:
                d_fmt = "%" + "%d" % self.data_width + "d ns  "
                lat += (d_fmt % (l * 1000),)
            else:
                d_fmt = "%" + "%d" % self.data_width + ".1f us  "
                lat += (d_fmt % l,)

        print(self.h_fmt % lat)
