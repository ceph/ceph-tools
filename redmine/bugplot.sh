#! /bin/bash
#
# this script (meant to be run before bugs.plot) just
# sets the base filenames.

{
	echo "BASE = \"$1\"";
	echo "INFILE = \"$1\"";
	echo "load \"bugs.plot\"";
} | gnuplot
