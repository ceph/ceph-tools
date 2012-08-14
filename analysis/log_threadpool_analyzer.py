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
from datetime import datetime,timedelta

threads = {}
waits = {}
wc = 0
waitstate = False
sdate = ""
edate = ""

df = "%Y-%m-%d %H:%M:%S.%f"
dsf = "%Y-%m-%d %H:%M:%S"

def fcell(item, width):
    if isinstance(item, str):
        return item.rjust(width)[:width]
    if isinstance(item, int):
        return str(item).rjust(width)[:width]
    if isinstance(item, float):
       return ("%.2f" % item).rjust(width)[:width]

filename = sys.argv[1]
f = open(filename, 'rb')
for line in f:
    words = line.split()
    date = "%s %s" % (words[0], words[1])

    edate = date
    if sdate == "":
       sdate = date
 
    if words[4] == 'FileStore::op_tp' and words[5] == 'worker':
        # Handle wait periods
        if waitstate == True:
            waits[wc]['done'] = date
            waitstate = False
            wc += 1
        if words[6] == 'waiting':
            waits[wc] = {}
            waits[wc]['start'] = date
            waitstate = True
        elif words[6] == "wq":
            blah,thread = words[7].split('::', 1)
            if thread not in threads:
                threads[thread] = {}
            action = words[8]
            item = words[10]

            if item not in threads[thread]:
                threads[thread][item] = {}
            length = len(threads[thread][item])
            if action == 'start':
                length += 1;
                threads[thread][item][length] = {}
            
            threads[thread][item][length][action] = date

seconds = {}
for wait in waits:
    if 'start' not in waits[wait] or 'done' not in waits[wait]:
        continue
    start = datetime.strptime(waits[wait]['start'], df)
    done = datetime.strptime(waits[wait]['done'], df)

    while (done - start).total_seconds() > 0:
        second = start.strftime(dsf)
        nt = start.replace(microsecond=0) + timedelta(seconds=1)
        if (nt > done):
            nt = done
        delta = nt - start
        
        if second not in seconds:
            seconds[second] = {}
        if 'wait' in seconds[second]:
            seconds[second]['wait'] += delta.total_seconds()
        else:
            seconds[second]['wait'] = delta.total_seconds()
        start = nt

for thread in threads:
    for item in threads[thread]:
        for instance in threads[thread][item]:
            if 'start' not in threads[thread][item][instance] or 'done' not in threads[thread][item][instance]:
                continue

            start = datetime.strptime(threads[thread][item][instance]['start'], df)
            done = datetime.strptime(threads[thread][item][instance]['done'], df)

            while (done - start).total_seconds() > 0: 
                second = start.strftime(dsf)

                if second not in seconds:
                    seconds[second] = {}
                if 'threads' not in seconds[second]:
                    seconds[second]['threads'] = {}
                if thread not in seconds[second]['threads']:
                    seconds[second]['threads'][thread] = {}
                    
                nt = start.replace(microsecond=0) + timedelta(seconds=1)
                if (nt > done):
                    nt = done
                    if 'count' not in seconds[second]['threads'][thread]:
                        seconds[second]['threads'][thread]['count'] = 1
                    else:
                        seconds[second]['threads'][thread]['count'] += 1

                delta = nt - start

                if 'time' not in seconds[second]['threads'][thread]:
                    seconds[second]['threads'][thread]['time'] = delta.total_seconds()
                else:
                    seconds[second]['threads'][thread]['time'] += delta.total_seconds()

                start = nt


d = datetime.strptime(sdate, df).replace(microsecond=0)
ed = datetime.strptime(edate, df).replace(microsecond=0)
print fcell(" " * 19, 19), fcell("Waiting", 10),
for thread in sorted(threads):
    print fcell(thread, 10),
    print fcell(thread, 10),
    print fcell(thread, 10),
print ""
print fcell("TiemStamp", 19), fcell("% Time", 10),
for thread in sorted(threads):
    print fcell("% Time", 10),
    print fcell("Op Count", 10),
    print fcell("Avg Op Tm", 10),
print ""
print fcell("-" * 19, 19), fcell("-" * 10, 10),
for thread in sorted(threads):
    print fcell("-" * 10, 10),
    print fcell("-" * 10, 10),
    print fcell("-" * 10, 10),
print ""

while d <= ed:
    second = d.strftime(dsf)
    sdict = seconds.get(second, {})
    print fcell(second,19),
    wait = "%.2f%%" % float(sdict.get('wait', 0) * 100)
    print fcell(wait, 10),
    for thread in sorted(threads):
        trdict = sdict.get('threads', {})
        tdict = trdict.get(thread, {})
        util = float(tdict.get('time', 0))
        count = tdict.get('count', 0)
        print fcell("%.2f%%" % float(util * 100), 10),
        print fcell(count, 10),
        avgoptime = "N/A"
        if count > 0:
            avgoptime = 1000 * util / count
        print fcell(avgoptime, 10), 
    print ""

    d += timedelta(seconds=1)
