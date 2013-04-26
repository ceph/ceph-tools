#! /bin/bash
#
# Gnuplot scripts cannot accept command line parameters.
#
# This script (meant to be run before a generic plotting script)
# sets input and output file names, and then loads the plot script.

if [ -z "$1" ]
then
	echo "usage: bugplot.sh base [plotscript]"
	exit 1
fi

if [ -n "$2" ]
then
	plot="$2"
else
	plot="bugs.plot"
fi

{
	echo "BASE = \"$1\"";
	echo "INFILE = \"$1\"";
	echo "load \"$plot\"";
} | gnuplot 2>&1 | grep -v arial
