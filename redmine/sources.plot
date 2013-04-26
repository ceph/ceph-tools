#! /usr/bin/gnuplot
#
# generate plots of numbers of bugs submitted in each time period
# broken down by source and tracker-type or priority
#
# usage:
#	gnuplot weekly.plot sources.plot 
#
# expected input:
#	date bucket dev qa com-dev com-user none
#
# This plot file does not care what the time unit is, it just uses 
# column 1 as a label
#
# TODO
#
#  (1)	Having this script know what the names and colors of
#	the issue classifications ties this to the database
#	and the reduction script.  Much better would be if
#	the reduction script could pass the titles and colors
#	in to me.  Maybe 'lc variable' can help here.
#
# NOTE:
#	the variable BASE, which controls input and output file names,
#	must have been initialized ... e.g.
#		BASE = "Urgent"
#		INFILE = "sources.".BASE
#	output files will have names of the form $BASE-{new,fix,net}.png
# 

print "Processing input file: ".INFILE." to create output ".BASE."-src.png"

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

set output BASE."-src.png"
set title BASE." Issue Sources";
plot	INFILE	u 3:xticlabels(1) 			\
			t "Developers"	lc rgb 'green',	\
	''	u 4	t "Q/A"		lc rgb 'blue',  \
	''	u 5	t "Comm (dev)"	lc rgb 'yellow',\
	''	u 6	t "Comm (usr)"	lc rgb 'orange',\
	''	u 7	t "Support"	lc rgb 'red',	\
	''	u 8	t "other"	lc rgb 'grey',	\
	''	u 9	t "none"	lc rgb 'white';
