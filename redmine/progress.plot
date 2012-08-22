#! /usr/bin/gnuplot
#
# generate plots of outstanding and done work, 
# per project, over time
#
# usage:
#	gnuplot progress.plot bugdata
#
# expected input format:
# 	date	tasks-todo tasks-done points-todo points-done sprint
#
# This plot file does not care what the time unit is, it just uses 
# column 1 as a label
#
# NOTE:
#	the variable BASE, which controls input and output file names,
#	must have been initialized ... e.g.
#		BASE = "weekly"
#		INFILE = "bugs.".BASE
#	output files will have names of the form $BASE-{new,fix,net}.png
# 

BASE="CY2012"
INFILE="/tmp/bugtemp/".BASE.".out"
OUTFILE="/tmp/bugtmp/".BASE.".png"

print "Processing input file: ".INFILE." to create output ".BASE."-{points,tasks}.png"

# output to png files
set term png font 

# things usually get busier to the right
set key left top

# dates print better rotated
set xtics out nomirror rotate

# stacked histograms
set ytics out nomirror
set style data histograms
set style histogram rowstacked
set style fill solid border -1
set boxwidth 0.8 relative


set output BASE."-points.png"
set ylabel "Points"
set title "Complete vs TODO (points) for ".BASE
plot	INFILE	u 4:xticlabels(6) t 'points remaining' lc rgb 'red',\
	''	u 5		  t 'points complete'  lc rgb 'green

set output BASE."-tasks.png"
set ylabel "Tasks"
set title "Complete vs TODO (tasks) for ".BASE
plot	INFILE	u 2:xticlabels(6) t 'tasks remaining' lc rgb 'red',\
	''	u 3		  t 'tasks complete'  lc rgb 'green
