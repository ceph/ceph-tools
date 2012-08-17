#!/usr/bin/python

# This program is used to parse system calls generated via stracing a program
# like ceph-osd or test_filestore_workloadgen.
#
# strace invokation to use:
#
# strace -q -a1 -s0 -f -tttT -oOUT_FILE -e trace=file,desc,process,socket APPLICATION ARGUMENTS
#
# then run this like:
#
# strace_parser.py OUT_FILE

import os
import os.path
import re
import sys
import decimal
import datetime
from datetime import datetime

ops = ["writev", "syscall_306", "ftruncate", "openat", "open", "stat", "setxattr", "removexattr", "close", "lseek", "read", "write", "pwrite", "clone", "sync_file_range", "fsync", "getdents", "link", "unlink", "mkdir", "rmdir", "ioctl", "access", "fcntl", "rename"]
threads = {}
seconds = {}
writev_bucket = {}
first = 0

def fcell(item):
    if isinstance(item, str):
        return item.rjust(9)[:9]
    if isinstance(item, int):
        return str(item).rjust(9)[:9]
#    return str(item).rjust(9)[:9]
    if isinstance(item, float):
       return ("%.2f" % item).rjust(9)[:9]

last_sec = 0
filename = sys.argv[1]
f = open(filename, 'rb')
for line in f:
    line = ' '.join(line.split())
#    print line
    words = line.split(" ", 2)
    thread = words[0]
    unixtime = words[1].split(".")[0]
    if not (thread.isdigit() or unixtime.isdigit()):
        print "malformed line: %s" % line
        continue 
    
    if first == 0:
        first = int(unixtime)

    thread = words[0]
    if thread not in threads:
        threads[thread] = {}
    second = int(unixtime) - first
    for s in xrange(last_sec, second+1):
        if s not in seconds:
            seconds[s] = {}
            for thread in threads:
                seconds[s][thread] = {}
    last_sec = second

    if thread not in seconds[second]:
        seconds[second][thread] = {}

    op_string = words[2]
    found = False 
    for op in ops:
        add = False
        if op_string.startswith("<... %s " % op):
            found = True
            add = True
        elif op_string.startswith("%s(" % op): 
            found = True
            if "unfinished" not in op_string:
                add = True

        if add is True:
            regex = "(\<)(\d+\.\d+)(\>)"
            match = re.search(regex, op_string)
            latency = float(match.group(2))
            if op is "writev":
                regex = "(= )(\d+)( \<)"
                match = re.search(regex, op_string)
                return_code = int(match.group(2))
                if return_code not in writev_bucket:
                    writev_bucket[return_code] = 1
                else:
                    writev_bucket[return_code] += 1

            if op is "syscall_306":
                print "syscall_306 latency: %s" % latency
            if op not in seconds[second][thread]:
                seconds[second][thread][op] = {}
                seconds[second][thread][op]['count'] = 1
                seconds[second][thread][op]['latency'] = latency
                seconds[second][thread][op]['latsum'] = latency
            else:
                cur_count = seconds[second][thread][op]['count']
                cur_latency = seconds[second][thread][op]['latency']
                seconds[second][thread][op]['count'] = cur_count + 1
                seconds[second][thread][op]['latency'] = (cur_latency * cur_count + latency) / (cur_count + 1)
                seconds[second][thread][op]['latsum'] += latency

    if found is False:
        print "Didn't find op in: %s" % op_string

print fcell("second"),
for op in ops:
    print fcell(op),
print ""

for second in seconds:
    counts = {}
    latencies = {}
    latsums = {}
    for op in ops:
        counts[op] = 0
        latencies[op] = 0
        latsums[op] = 0

    for thread in seconds[second]:
        th = seconds[second][thread]
        for op in ops:
            opdict = th.get(op, {})
            cur_count = counts[op]
            cur_latency = latencies[op]
            counts[op] += opdict.get('count', 0)
            if counts[op] > 0:
                latencies[op] = (cur_latency * cur_count + opdict.get('latency', 0)) / counts[op]
            latsums[op] += opdict.get('latsum', 0)                  

    print fcell(second),
    for op in ops:
        if op is "writev":
            print fcell(counts.get(op, 0)),
        else: 
            print fcell(latsums.get(op, 0)),
    print ""
print ""
print "writev call statistics:"
print ""
print "Write Size, Frequency"
for key in sorted(writev_bucket.keys()):
    print "%s, %s" % (key, writev_bucket[key])
