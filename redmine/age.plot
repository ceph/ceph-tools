#! /usr/bin/gnuplot
#
# generate plots of time to fix and bug ages
# broken down by tracker-type or priority
#
# usage:
#	gnuplot age.plot
#
# expected input format:
# 	bucket	urgent high normal low feature support cleanup tasks doc ...
#		first set of columns is for time to fix
#		second set of columns is for age (of unfixed) issues
#
# The bucket (in column 1) is merely a label
#
# TODO
#  	Having this script know what the names and colors of
#	the issue classifications ties this to the database
#	and the reduction script.  Much better would be if
#	the reduction script could pass the titles and colors
#	in to me.  Maybe 'lc variable' can help here.
#
# NOTE:
#	the variable BASE, which controls input and output file names,
#	must have been initialized ... e.g.
#		BASE = "weekly"
#		INFILE = "bugs.".BASE
#	output files will have names of the form $BASE-{ttf,age}.png
# 

BASE="all"
INFILE="all"

print "Processing input file: ".INFILE." to create output ".BASE."-{ttf,age}.png"

# output to png files
set term png 

# things usually get busier to the right
set key left top

set xtics out nomirror 
set ytics out nomirror

set style data linespoints

set output BASE."-ttf.png"
set title "Issue Fix Times (days)";
plot	INFILE	u 2:xticlabels(1) 			\
			t "Immediate"	lc rgb 'violet',\
	''	u 3	t "Urgent"	lc rgb 'red',	\
	''	u 4	t "High"	lc rgb 'pink',	\
	''	u 5	t "Normal"	lc rgb 'orange',\
	''	u 6	t "Low"		lc rgb 'yellow',\
	''	u 7	t "Feature"	lc rgb 'green',	\
	''	u 9	t "Support"	lc rgb 'blue',	\
	''	u 9	t "Cleanup"	lc rgb 'cyan',	\
	''	u 10	t "Tasks"	lc rgb 'white',	\
	''	u 11	t "Doc"		lc rgb 'grey';

set output BASE."-age.png"
set title "Issue Ages (days)";
plot	INFILE	u 12:xticlabels(1) 			\
			t "Immediate"	lc rgb 'violet',\
	''	u 13	t "Urgent"	lc rgb 'red',	\
	''	u 14	t "High"	lc rgb 'pink',	\
	''	u 15	t "Normal"	lc rgb 'orange',\
	''	u 16	t "Low"		lc rgb 'yellow',\
	''	u 17	t "Feature"	lc rgb 'green',	\
	''	u 18	t "Support"	lc rgb 'blue',	\
	''	u 19	t "Cleanup"	lc rgb 'cyan',	\
	''	u 20	t "Tasks"	lc rgb 'white',	\
	''	u 21	t "Doc"		lc rgb 'grey';
