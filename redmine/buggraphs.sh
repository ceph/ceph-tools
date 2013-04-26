#!/bin/bash
#
# process a Redmine bug dump (produced by redmine_dump.pl) to extract
# and plot interesting statistics 

# input file to process
if [ -z "$1" ]
then
	echo "Usage: buggraphs.sh dumpfile [target directory]"
	exit 1
else
	bugdump="$1"
fi

# where to put our work products
if [ -z "$2" ]
then
	echo "Results can be found in: $TEMP"
	TEMP="/tmp/bugtemp.$$"
	mkdir $TEMP
else
	TEMP="$2"
fi

# limit how far back we go to keep the X axis readable
WSTART="40w"
MSTART="25m"

echo "Processing $bugdump for monthly statistics"
perl bugmunch.pl -s $MSTART $bugdump > $TEMP/monthly
if [ $? -ne 0 ] 
then
	echo "FATAL: error monthly bugmunch"
	exit 1
else
	./bugplot.sh $TEMP/monthly bugs.plot
fi

echo "Processing $bugdump for weekly statistics"
perl bugmunch.pl -w -s $WSTART $bugdump > $TEMP/weekly
if [ $? -ne 0 ] 
then
	echo "FATAL: error in weekly bugmunch"
	exit 1
else
	./bugplot.sh $TEMP/weekly bugs.plot
fi
perl bugmunch.pl -w -r $bugdump > $TEMP/bugstats.txt
if [ $? -ne 0 ] 
then
	echo "FATAL: error in weekly bugstats"
	exit 1
fi

echo "Processing $bugdump for source statistics"
perl sourcemunch.pl -w -s $WSTART $bugdump > $TEMP/sources
if [ $? -ne 0 ] 
then
	echo "FATAL: error in weekly sourcemunch"
	exit 1
else
	grep Urgent $TEMP/sources > $TEMP/Urgent
	./bugplot.sh $TEMP/Urgent sources.plot
	grep High $TEMP/sources > $TEMP/High
	./bugplot.sh $TEMP/High sources.plot
	grep Normal $TEMP/sources > $TEMP/Normal
	./bugplot.sh $TEMP/Normal sources.plot
	grep Feature $TEMP/sources > $TEMP/Feature
	./bugplot.sh $TEMP/Feature sources.plot
fi

echo "Processing $bugdump for age statistics"
perl bugage.pl $bugdump > $TEMP/all
if [ $? -ne 0 ] 
then
	echo "FATAL: error in bug age report"
	exit 1
else
	./bugplot.sh $TEMP/all age.plot
fi

# FIX we need to automatically generate a list of interesting sprints
#     (probably based on their dates)
echo "^2012"  > $TEMP/oldsprints
echo "^2013" >> $TEMP/oldsprints
echo "^v2"   >> $TEMP/oldsprints
echo "^v3"   >> $TEMP/oldsprints
echo "^v0.1" >> $TEMP/oldsprints
echo "^v0.2" >> $TEMP/oldsprints
echo "^v0.3" >> $TEMP/oldsprints

echo "Processing $bugdump for sprintly statistics"
perl sprintmunch.pl $bugdump | grep -v -f $TEMP/oldsprints > $TEMP/sprintly
if [ $? -ne 0 ] 
then
	echo "FATAL: error in sprintly report"
	exit 1
else
	./bugplot.sh $TEMP/sprintly sprints.plot
fi
