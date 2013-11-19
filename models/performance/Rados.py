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
This is intended to be able to simulate the overhead that
a remote RADOS client experiences for standard test loads

NOTE:

   All of the lower level models try to estimate single operation
   latency (at a request depth, with amortized costs for async
   operations) for a single resource (e.g. disk).

   This is a model for a parallel system.  I found it difficult
   to model parallel latencies, so I decided to do this one as a
   throughput model.  This is confusing because all of the quantities
   we are dealing with are latencies ... so when I do some baffling
   multiply or divide to a time, understand it as the inverse operation
   on a throughput.  I considered inverting everything to make these
   computations more obvious, but the before-and-after inversions
   were even more confusing.
"""

from units import *


class Rados:
    """ Performance Modeling RADOS Simulation. """

    nic_overhead = 0.00		# fraction of NIC we can't use
    null_resp = 1000        # NOP response time
    warnings = ""           # save these up for reporting later

    # FIX - front and back should be NIC simulations rather than speeds
    def __init__(self, filestore,
                 front_nic=10 * GIG, back_nic=10 * GIG,
                 nodes=1, osd_per_node=1):
        """ create a RADOS simulation
            filestore -- simulation
            front_nic -- front side NIC speed
            back_nic -- back side NIC speed
            nodes -- number of nodes in the cluster
            osd_per_node -- number of OSDs per node
        """

        self.filestore = filestore
        self.num_nodes = nodes
        self.num_osds = nodes * osd_per_node
        self.osd_per_node = osd_per_node
        self.frontside = (1 - self.nic_overhead) * front_nic / 8
        self.backside = (1 - self.nic_overhead) * back_nic / 8

    def network(self, bsize, bw):
        """ expected time to do send/receive a message
            bsize -- size of the message to be sent
            bw -- NIC bandwidth for this operation
        """
        return SECOND * bsize / bw

    def read(self, bsize, obj_size, nobj=2500, depth=1, clients=1):
        """ average time for reads (modeled as throughput)
            bsize -- size of the read
            objsize -- size of the object we are reading from
            nobj -- number of objects over which reads are spread
            depth -- number of concurrent requests per client
            clients -- number of parallel clients generating load
        """

        # how does spreading affect depth, numobj
        nobj /= self.num_osds
        if depth * clients < self.num_osds:
            d = 1
        else:
            d = depth * clients / self.num_osds

        # at what rate can filestore process these requests
        ftime = self.filestore.read(bsize, obj_size, depth=d, nobj=nobj)
        ftime /= self.num_osds

        # at what rate can (shared) server NIC return responses
        stime = self.network(
            bsize,
            self.frontside * self.num_nodes / self.osd_per_node)

        # at what rate can (a single) client NIC accept responses
        ctime = self.network(bsize, self.frontside * clients)

        # RADOS throughput is the least of these
        if stime > ctime:
            net_worst = stime
            slowpoke = "server"
        else:
            net_worst = ctime
            slowpoke = "client"
        if net_worst > ftime:
            worst = net_worst
            if "byte reads" not in self.warnings:
                msg = "\n\t%s NIC caps throughput for %d byte reads"
                self.warnings += msg % (slowpoke, bsize)
        else:
            worst = ftime

        # and we have to add in something for the req/response
        return worst + self.null_resp / depth

    def write(self, bsize, obj_size, nobj=2500, depth=1, clients=1, copies=1):
        """ average time for object writes
            bsize -- size of the write
            objsize -- size of the object we are reading to
            nobj -- number of objects over which reads are spread
            depth -- number of concurrent requests per client
            clients -- number of parallel clients generating load
            copies -- number of copies being made
        """

        # how does spreading affect depth, numobj
        nobj *= float(copies) / self.num_osds
        if depth * clients * copies < self.num_osds:
            d = 1
        else:
            d = depth * clients * copies / self.num_osds

        # at what rate can filestores process these requests
        ftime = self.filestore.write(bsize, obj_size, depth=d, nobj=nobj)
        ftime /= self.num_osds  # many operate in parallel
        ftime *= copies         # but they are also making copies

        # at what rate can (shared) primary server accept/replicate
        fsbw = self.frontside * self.num_nodes / self.osd_per_node
        bsbw = self.backside * self.num_nodes / self.osd_per_node
        stime = self.network(bsize, fsbw)
        stime += (copies - 1) * self.network(bsize, bsbw)

        # at what rate can (a single) client NIC generate writes
        ctime = self.network(bsize, self.frontside * clients)

        # RADOS throughput is the least of these
        if stime > ctime:
            net_worst = stime
            slowpoke = "server"
        else:
            net_worst = ctime
            slowpoke = "client"
        if net_worst > ftime:
            worst = net_worst
            if "byte writes" not in self.warnings:
                msg = "\n\t%s NIC caps throughput for %d-copy %d byte writes"
                self.warnings += msg % (slowpoke, copies, bsize)
        else:
            worst = ftime

        # and we have to add in something for the req/response
        return worst + self.null_resp / depth

    def create(self, depth=1):
        """ new object creation """

        return self.op_latency + self.filestore.create()

    def delete(self, depth=1):
        """ object deletion """

        return self.op_latency + self.filestore.delete()


# helper function to create filestore simulations
def makerados(filestore, dict):
    """ instantiate a filestore simulation from a dict
        datafs -- fs for data
        journalfs -- fs for journal
        dict -- other parameters
            osd_per_node: number of OSD running on each storage node
    """

    dflt = {        # default cluster parameters
        'front': 1 * GIG,
        'back': 1 * GIG,
        'nodes': 1,
        'osd_per_node': 1,
    }

    front = dict['front'] if 'front' in dict else dflt['front']
    back = dict['back'] if 'back' in dict else dflt['back']
    nodes = dict['nodes'] if 'nodes' in dict else dflt['nodes']
    osd_per = dict['osd_per_node'] if 'osd_per_node' in dict \
        else dflt['osd_per_node']

    rados = Rados(filestore, front_nic=front, back_nic=back,
                  nodes=nodes, osd_per_node=osd_per)
    return rados


from Report import Report


def radostest(rados, dict, descr=""):
    """ run a set of test described by a dict
        dict
            SioRdepth - range of depths
            SioRbs: range of block sizes
            SioRsize - object size
            SioRnobj - number of objects to read
            SioRcopies - range of write reduncancies
            SioRclient - range of number of test instances
            SioInst - range of instances per client
    """

    dflt = {        # default test parameters
        'SioRdepth': [1, 16],
        'SioRbs': [4096, 128 * 1024, 4096 * 1024],
        'SioRsize': 16 * MEG,
        'SioRnobj': 2500,
        'SioRcopies': [1],
        'SioRclient': [1],
        'SioRinst': [1],
        'SioRmisc': False,
    }

    # gather up the parameters
    depths = dict['SioRdepth'] if 'SioRdepth' in dict else dflt['SioRdepth']
    bsizes = dict['SioRbs'] if 'SioRbs' in dict else dflt['SioRbs']
    sz = dict['SioRsize'] if 'SioRsize' in dict else dflt['SioRsize']
    no = dict['SioRnobj'] if 'SioRnobj' in dict else dflt['SioRnobj']
    cp = dict['SioRcopies'] if 'SioRcopies' in dict else dflt['SioRcopies']
    cl = dict['SioRclient'] if 'SioRclient' in dict else dflt['SioRclient']
    inst = dict['SioRinst'] if 'SioRinst' in dict else dflt['SioRinst']
    misc = dict['SioRmisc'] if 'SioRmisc' in dict else dflt['SioRmisc']

    for x in cp:                    # number of copies
        for c in cl:                # number of clients
            for i in inst:          # number of instances per client
                for d in depths:    # requests per instance
                    msg = "smalliobench-rados (%dx%d)" % \
                        (rados.num_nodes, rados.osd_per_node)
                    msg += ", %d copy" % x
                    msg += ", clients*instances*depth=(%d*%d*%d)" % (c, i, d)
                    print(msg)
                    print("\t%s, nobj=%d, objsize=%d" % (descr, no, sz))

                    if misc:
                        tc = rados.create(depth=1)
                        td = rados.delete(depth=1)
                        r = Report(("create", "delete"))
                        r.printHeading()
                        r.printIOPS(1, (SECOND / tc, SECOND / td))
                        r.printLatency(1, (tc, td))
                        print("")

                    r = Report(("rnd read", "rnd write"))
                    r.printHeading()
                    for bs in bsizes:
                        trr = rados.read(bs, sz, nobj=no, clients=c,
                                         depth=i * d)
                        trw = rados.write(bs, sz, nobj=no, clients=c,
                                          depth=i * d, copies=x)

                        # compute the corresponding bandwidths
                        brr = bs * SECOND / trr
                        brw = bs * SECOND / trw
                        r.printBW(bs, (brr, brw))

                        # compute the corresponding IOPS
                        irr = SECOND / trr
                        irw = SECOND / trw
                        r.printIOPS(0, (irr, irw))
                        #r.printLatency(o, (trr, trw))
                    print("")

#
# instantiate a RADOS cluster and run a set of basic tests
#
if __name__ == '__main__':

        from SimDisk import makedisk
        disk = makedisk({'device': 'disk'})
        from SimFS import makefs
        fs = makefs(disk, {})
        from FileStore import makefilestore
        fst = makefilestore(fs, fs, {})
        rados = makerados(fst, {})

        msg = "data FS (%s on %s), journal " % \
            (fst.data_fs.desc, fst.data_fs.disk.desc)
        if fst.journal_fs is None:
            msg += "on data disk"
        else:
            msg += "(%s on %s)" % \
                (fst.journal_fs.desc, fst.journal_fs.disk.desc)

        radostest(rados, {}, descr=msg)
