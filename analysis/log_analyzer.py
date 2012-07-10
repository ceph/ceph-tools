#!/usr/bin/python

import gzip
import os
import os.path
import re
import sys
import datetime
from datetime import datetime

tracker_regex = re.compile('.*reqid: (.+), seq: ([0-9]+), time: (\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d\.\d\d\d\d\d\d), event: (.*), request: (.*)')

def wrapgz(gfilename):
    def retval():
        gfile = gzip.open(gfilename, 'rb')
        gfile.__exit__ = lambda: gfile.close()
        return gfile
    return (gfilename, retval)

def wrap(filename):
    def retval():
        nfile = open(filename, 'rb')
        return nfile
    return (filename, retval)

def get_logs(path):
    output = {}
    output['config'] = lambda: open(os.path.join(path, 'config.yaml'), 'r')
    output['osd'] = {}
    output['client'] = {}
    for path, dirs, files in os.walk(os.path.abspath(path)):
        for filename in files:
            match = re.match('osd.([0-9]+).log.gz', filename)
            if match:
                fn = os.path.join(path, filename)
                output['osd'][int(match.group(1))] = wrapgz(
                    os.path.join(path, filename))
            match = re.match('osd.([0-9]+).log', filename)
            if match and not int(match.group(1)) in output['osd']:
                fn = os.path.join(path, filename)
                output['osd'][int(match.group(1))] = wrap(
                    os.path.join(path, filename))
            match = re.match('client.([0-9]+).log.gz', filename)
            if match:
                fn = os.path.join(path, filename)
                output['client'][int(match.group(1))] = wrapgz(
                    os.path.join(path, filename))
            match = re.match('client.([0-9]+).log', filename)
            if match and not int(match.group(1)) in output['client']:
                fn = os.path.join(path, filename)
                output['client'][int(match.group(1))] = wrap(
                    os.path.join(path, filename))
    return output

def parse_tracker_line(line):
    retval = {}
    match = tracker_regex.match(line)
    if match:
        retval['reqid'] = match.group(1)
        retval['seq'] = int(match.group(2))
        retval['time'] = datetime.strptime(
            match.group(3), '%Y-%m-%d %H:%M:%S.%f'
            )
        retval['event'] = match.group(4)
        retval['request'] = match.group(5)
        return retval
    return None

class Request:
    def __init__(self):
        self.parsed = []
        self.events = []
        self.last_event = None
        self.first_event = None
        self._primary = -1
        self.osds = []
        

    def add_event(self, parsed):
        if self.parsed == []:
            self.last_event = parsed['time']
            self.first_event = parsed['time']
        self.parsed.append(parsed)
        self.events.append((parsed['time'], parsed['event'], parsed['osd']))
        self.events.sort()
        if self.last_event < parsed['time']:
            self.last_event = parsed['time']
        if self.first_event > parsed['time']:
            self.first_event = parsed['time']
        if parsed['event'] == 'op_applied':
            self._primary = parsed['osd']
        if parsed['osd'] not in self.osds:
            self.osds.append(parsed['osd'])
            self.osds.sort()

    def duration(self):
        return (self.last_event - self.first_event).total_seconds()

    def __repr__(self):
        return str(self.events) + " " + \
               str(self.duration()) + " " + self.parsed[0]['reqid']

    def pretty_print(self):
        outstr = "reqid: %s, duration: %s"%(
            self.parsed[0]['reqid'],str(self.duration()))
        outstr += "\n=====================\n"
        for (time, event, osd) in self.events:
            outstr += "%s (osd.%s): %s\n"%(str(time), str(osd), event)
        outstr += "=====================\n"
        return outstr

    def primary(self):
        return self._primary

    def replicas(self):
        return self.osds
        

requests = {}

logs = get_logs(sys.argv[1])

for i, (fn, func) in logs['osd'].iteritems():
    with func() as f:
        for line in f.readlines():
            parsed = parse_tracker_line(line)
            if not parsed or parsed['reqid'] == 'unknown.0.0:0':
                continue
            parsed['osd'] = i
            if parsed['reqid'] not in requests:
                requests[parsed['reqid']] = Request()
            requests[parsed['reqid']].add_event(parsed)

all_requests = [(i.duration(), i) for i in requests.itervalues()]
all_requests.sort()

pairs = {}
for _, i in all_requests:
    if tuple(i.replicas()) not in pairs:
        pairs[tuple(i.replicas())] = 0
    pairs[tuple(i.replicas())] += 1
print pairs 

osds = {}
for _, i in all_requests:
    if i.primary() not in osds:
        osds[i.primary()] = 0
    osds[i.primary()] += 1

print osds

for _, i in all_requests[:-100:-1]:
    print i.pretty_print()
