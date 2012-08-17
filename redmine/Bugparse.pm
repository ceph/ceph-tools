#
# module: Bugparse
#	
# purpose:
#	to figure out which columns of a bug dump contain
#	which information, ideally driven by a comment header
#
# the supported literal column keys are:
# 	bugid
# 	category
# 	closed
# 	created
#	history
#	points
# 	priority
#	project
# 	source
#	status
#	tags
# 	type
# 	version
#
use warnings;
use strict;

package Bugparse;

require Exporter;
my @ISA	= qw(Exporter);
my @EXPORT = qw(parser);

#
# parse a line that is presumed to contain column headings
# and initialize a mapping from column names to numbers
#
sub parser {
	my $str = substr( $_[0], 1 );
	my @cols = split( '\t', $str );
	my %colMap = ();

	# try to get every column
	for( my $i = 0; $i < scalar @cols; $i++ ) {
		$cols[$i] =~ s/^\s+//;
		$cols[$i] =~ s/\s+$//;

		if ($cols[$i] eq 'bugid') {
			$colMap{'bugid'} = $i;
		} elsif ($cols[$i] eq 'category') {
			$colMap{'category'} = $i;
		} elsif ($cols[$i] eq 'issue type') {
			$colMap{'type'} = $i;
		} elsif ($cols[$i] eq 'source') {
			$colMap{'source'} = $i;
		} elsif ($cols[$i] eq 'prty') {
			$colMap{'priority'} = $i;
		} elsif ($cols[$i] eq 'version') {
			$colMap{'version'} = $i;
		} elsif ($cols[$i] eq 'created') {
			$colMap{'created'} = $i;
		} elsif ($cols[$i] eq 'closed') {
			$colMap{'closed'} = $i;
		} elsif ($cols[$i] eq 'status') {
			$colMap{'status'} = $i;
		} elsif ($cols[$i] eq 'history') {
			$colMap{'history'} = $i;
		} elsif ($cols[$i] eq 'points') {
			$colMap{'points'} = $i;
		} elsif ($cols[$i] eq 'project') {
			$colMap{'project'} = $i;
		} elsif ($cols[$i] eq 'tags') {
			$colMap{'tags'} = $i;
		} 
		# don't sweat unrecognized columns
	}

	return( %colMap );
}

1;
