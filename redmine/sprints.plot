#! /usr/bin/gnuplot
#
# generate plots of numbers of issues assigned to and fixed to each version
# broken down by tracker-type or priority
#
# usage:
#	gnuplot sprints.plot
#
# expected input format:
#	version name
# 	assigned: urgent high normal low feature support cleanup tasks doc
# 	fixed:	  urgent high normal low feature support cleanup tasks doc
#
#  (1)	Having this script know what the names and colors of
#	the issue classifications ties this to the database
#	and the reduction script.  Much better would be if
#	the reduction script could pass the titles and colors
#	in to me.  Maybe 'lc variable' can help here.
#

print "Processing input file: ".INFILE." to create output ".BASE."-{asgn,fix,spill,net}.png"

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

set output BASE."-asgn.png"
set title "Issues assigned to each sprint";
plot	INFILE	u 3:xticlabels(1) 			\
			t "Immediate"	lc rgb 'violet',\
	''	u 4	t "Urgent"	lc rgb 'red',	\
	''	u 5	t "High"	lc rgb 'pink',	\
	''	u 6	t "Normal"	lc rgb 'orange',\
	''	u 7	t "Low"		lc rgb 'yellow',\
	''	u 8	t "Feature"	lc rgb 'green',	\
	''	u 9	t "Support"	lc rgb 'blue',	\
	''	u 10	t "Cleanup"	lc rgb 'cyan',	\
	''	u 11	t "Tasks"	lc rgb 'white',	\
	''	u 12	t "Doc"		lc rgb 'grey';

set output BASE."-fix.png"
set title "Issues fixed in each sprint";
plot	INFILE	u 14:xticlabels(1) 			\
			t "Immediate"	lc rgb 'violet',\
	''	u 15	t "Urgent"	lc rgb 'red',	\
	''	u 16	t "High"	lc rgb 'pink',	\
	''	u 17	t "Normal"	lc rgb 'orange',\
	''	u 18	t "Low"		lc rgb 'yellow',\
	''	u 19	t "Feature"	lc rgb 'green',	\
	''	u 20	t "Support"	lc rgb 'blue',	\
	''	u 21	t "Cleanup"	lc rgb 'cyan',	\
	''	u 22	t "Tasks"	lc rgb 'white',	\
	''	u 23	t "Doc"		lc rgb 'grey';

set output BASE."-spill.png"
set title "Breakdown of unaccomplished work in each sprint";
plot	INFILE	u ($3-$14):xticlabels(1) 			\
				t "Immediate"	lc rgb 'violet',\
	''	u ($4-$15)	t "Urgent"	lc rgb 'red',	\
	''	u ($5-$16)	t "High"	lc rgb 'pink',	\
	''	u ($6-$17)	t "Normal"	lc rgb 'orange',\
	''	u ($7-$18)	t "Low"		lc rgb 'yellow',\
	''	u ($8-$19)	t "Feature"	lc rgb 'green',	\
	''	u ($9-$20)	t "Support"	lc rgb 'blue',	\
	''	u ($10-$21)	t "Cleanup"	lc rgb 'cyan',	\
	''	u ($11-$22)	t "Tasks"	lc rgb 'white',	\
	''	u ($12-$23)	t "Doc"		lc rgb 'grey';

set output BASE."-net.png"
set title "Committed vs Accomplished for each sprint";
plot	INFILE	u 13:xticlabels(1) 			\
				t "fixed"	lc rgb 'green'  ,\
	''	u ($2-$13)	t "not fixed"	lc rgb 'red' ;
