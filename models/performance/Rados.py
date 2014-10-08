#
# This is intended to be able to simulate the overhead that
# a remote RADOS client experiences for standard test loads
#
# NOTE:
#
#   All of the lower level models try to estimate single operation
#   latency (at a request depth, with amortized costs for async
#   operations) for a single resource (e.g. disk).
#
#   This is a model for a parallel system.  I found it difficult
#   to model parallel latencies, so I decided to do this one as a
#   throughput model.  This is confusing because all of the quantities
#   we are dealing with are latencies ... so when I do some baffling
#   multiply or divide to a time, understand it as the inverse operation
#   on a throughput.  I considered inverting everything to make these
#   computations more obvious, but the before-and-after inversions
#   were even more confusing.
#

# useful unit multipliers
GIG = 1000000000


class Rados(object):
    """ Performance Modeling RADOS Simulation. """

    nic_overhead = 0.00		# fraction of NIC we can't use
    null_resp = 1000        # NOP response time
    warnings = ""           # save these up for reporting later

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
        SECOND = 1000000
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
        stime = self.network(bsize,
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
