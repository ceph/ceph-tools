#!/usr/bin/perl
#
# script: relmunch
#	
# purpose:
#	to read through a raw bug list and generate
#	per release targeted/fixed counts
#
# output:
#	one row per release with a
#		name of release
#		number of issues accepted per category
#		number of issues fixed per category
#
use warnings;
use strict;
use Carp;

use Getopt::Std;
use File::Basename;
use Time::Local;

sub usage()
{	
	print STDERR "Usage: relmunch.pl [switches] [file ...]\n";
	print STDERR "        -s date .... report start date\n";
	print STDERR "        -e date .... report end date\n";
	print STDERR "        -p prefix .. prefix for output file names\n";
}

# parameters
my $prefix;		# output file prefix
my $start_date;		# report starting date
my $end_date;		# report end date

#
# FIX: this shouldn't be hard coded, but I should find a way to
#	put them in/get them from the RedMine dump.  The trick is
#	that the values I have chosen are a function of tracker-type 
#	and priority.
#
my @columns =	('Immediate', 'Urgent', 'High', 'Normal', 'Low',
		 'Feature', 'Support', 'Cleanup', 'Tasks', 'Documentation' );

#
# FIX: this shouldn't be hard coded, but should probably be read from
#	a product specific table that maps issue types and priorities
#	into reporting buckets.
#
sub get_bucket_name
{	(my $bugtype, my $priority) = ($_[0], $_[1]);
	return ($bugtype eq 'Bug') ? "$priority" : "$bugtype";
}


# accumulated information
my %versions = ();		# known versions
my %fixes = ();			# fix counts per version/type
my %assigns = ();		# assignment counts per version/type


#
# routine:	parse_date
#
# parameters:	date (mm/dd/yyyy)
#
# returns:	time value for that date
#
sub parse_date
{
	# discect the specified time
	(my $mon, my $day, my $year) = split( '/', $_[0] );
	return timegm( 0, 0, 0, $day, $mon-1, $year );
}

#
# routine:	get_period
#
# parameters:	date (mm/dd/yyyy)
#
# returns:	time value for the starting date of that period
#
sub get_period
{
	# discect the specified time
	(my $mon, my $day, my $year) = split( '/', $_[0] );

	my $when = timegm( 0, 0, 0, $day, $mon-1, $year );
	my ($s, $m, $h, $md, $mn, $yr, $wd, $yd, $dst) = gmtime( $when );
	$when -= $wd * 24 * 60 * 60;
	return $when;
}

#
# routine:	report
#
# purpose:
# 	generate a report of all bugs in all releases
#
sub report
{
	# print out the headers
	print "# ver";
	print " a-total";
	for (my $i = 0; $i < scalar @columns; $i++ ) {
		print " a-$columns[$i]";
	}
	print " f-total";
	for (my $i = 0; $i < scalar @columns; $i++ ) {
		print " f-$columns[$i]";
	}
	print "\n";

	# print out the data for each (valid) version
	my @fix_counts;
	my @asgn_counts;
	foreach my $ver (keys %versions) {
		if ($ver eq 'none') {
			next;
		}
		my $fixcount = 0;
		my $asgncount = 0;
		for (my $i = 0; $i < scalar @columns; $i++ ) {
			my $issue_type = $columns[$i];
			my $tag = "$ver-$issue_type";
			if (defined($fixes{$tag})) {
				$fix_counts[$i] = $fixes{$tag};
			} else {
				$fix_counts[$i] = 0;
			}
			$fixcount += $fix_counts[$i];

			if (defined($assigns{$tag})) {
				$asgn_counts[$i] = $assigns{$tag};
			} else {
				$asgn_counts[$i] = 0;
			}
			$asgncount += $asgn_counts[$i];
		}
	
		print "$ver";
		printf("\t%d", $asgncount);
		for (my $i = 0; $i < scalar @columns; $i++ ) {
			printf("\t%d", $asgn_counts[$i] );
		}
		printf("\t%d", $fixcount);
		for (my $i = 0; $i < scalar @columns; $i++ ) {
			printf("\t%d", $fix_counts[$i] );
		}
		print "\n";
	}
}

#
# routine:	process_newbug
#
# purpose:	
# 	accumulate another bug report
#
sub process_newbug
{	
	(my $created, my $bugtype, my $priority, my $fixed, my $ver, my $hist) = 
		($_[0], $_[1], $_[2], $_[3], $_[4], $_[5]);

	# make sure bug falls within the start/end window
	# FIX ... figure out what this even means in this report
	
	# figure out the accumulation bucket
	my $bucketname = get_bucket_name( $bugtype, $priority );

	# credit the version in which this bug was fixed
	if ($fixed ne "none" and $ver ne "none") {
		my $tag = "$ver-$bucketname";
		$versions{$ver} = $ver;
		if (defined($fixes{$tag})) {
			$fixes{$tag} = $fixes{$tag} + 1;
		} else {
			$fixes{$tag} = 1;
		}
	}

	# note every release in which we were supposed to fix it
	if ($hist ne "none") {
		my @rels = split(',',$hist);
		for ( my $i = 0; $i < scalar @rels; $i++ ) {
			my $tag = "$rels[$i]-$bucketname";
			$versions{$rels[$i]} = $rels[$i];
			if (defined($assigns{$tag})) {
				$assigns{$tag} = $assigns{$tag} + 1;
			} else {
				$assigns{$tag} = 1;
			}
		}
	}
}

#
# FIX ... this should be in a separate pm
#
# I have coded in a default input format, but ideally these
# column numbers should be initialized from a header comment
# on the first line of input.  Note that we know what info we
# are looking for so the comment names must exactly match the 
# expected strings.  It is OK if additional information is
# present, but this much is required.
#
my $col_bugid	= 0;	# bugid
my $col_category = 1;	# category
my $col_type	= 2;	# issue type
my $col_source	= 3;	# source
my $col_priority= 4;	# prty
my $col_version	= 5;	# version
my $col_created	= 6;	# created
my $col_closed	= 7;	# closed
my $col_history	= 8;	# history
my $col_status	= 9;	# status

my $col_numcols = 10;	# expected number of column matches
my $col_initialized = 0;

sub initialize_columns
{
	my $str = substr( $_, 1 );
	my @cols = split( '\t', $str );

	# try to get every column
	for( my $i = 0; $i < scalar @cols; $i++ ) {
		$cols[$i] =~ s/^\s+//;
		$cols[$i] =~ s/\s+$//;

		if ($cols[$i] eq 'bugid') {
			$col_bugid = $i;
			$col_initialized++;
		} elsif ($cols[$i] eq 'category') {
			$col_category = $i;
			$col_initialized++;
		} elsif ($cols[$i] eq 'issue type') {
			$col_type = $i;
			$col_initialized++;
		} elsif ($cols[$i] eq 'source') {
			$col_source = $i;
			$col_initialized++;
		} elsif ($cols[$i] eq 'prty') {
			$col_priority = $i;
			$col_initialized++;
		} elsif ($cols[$i] eq 'version') {
			$col_version = $i;
			$col_initialized++;
		} elsif ($cols[$i] eq 'created') {
			$col_created = $i;
			$col_initialized++;
		} elsif ($cols[$i] eq 'closed') {
			$col_closed = $i;
			$col_initialized++;
		} elsif ($cols[$i] eq 'status') {
			$col_status = $i;
			$col_initialized++;
		} elsif ($cols[$i] eq 'history') {
			$col_history = $i;
			$col_initialized++;
		} else {
			print STDERR "Unrecognized column header ($cols[$i])\n";
			return;
		}
	}

	# if we didn't find what we expected, we're hosed
	if ($col_initialized != $col_numcols) {
		die( "only found $col_initialized/$col_numcols in $str" );
	}
}

#
# routine:	process_file
#
# purpose:	
# 	to read the lines of an input file and pass the non-comments
# 	to the appropriate accumulation routines.
#
# expected input
#	 bugid cat type prty vers closed created_on updated_on history status
#
sub process_file
{	(my $file) = ($_[0]);

	while( <$file> ) {
		if (/^#/) {	# ignore comments
			if (!$col_initialized) {
				initialize_columns($_);
			}
			next;
		} else {
			# carve it into tab separated fields
			my @fields = split( '\t', $_ );
			
			# remove any leading or trailing blanks
			for ( my $i = 0; $i < scalar @fields; $i++ ) {
				$fields[$i] =~ s/^\s+//;
				$fields[$i] =~ s/\s+$//;
			}

			process_newbug( $fields[$col_created], $fields[$col_type], 
					$fields[$col_priority], $fields[$col_closed],
					$fields[$col_version], $fields[$col_history] );
		}
	}
}


#
# routine:	main
#
# purpose:
#	process arguments
#	figure out what operations we are supposed to do
#	perform them
#
# notes:
#	we require a command just to make sure the caller
#	knows what he is doing
#
sub main
{	
	# parse the input parameters
	my %options = ();
	if (!getopts('s:e:p:', \%options)) {
		usage();
		exit(1);
	}

	# see what our reporting period is
	$start_date = defined( $options{'s'} ) ? get_period($options{'s'}) : 0;
	$end_date   = defined( $options{'e'} ) ? get_period($options{'e'}) : time();

	# see if we have a specified output file prefix
	$prefix = defined( $options{'p'} ) ? $options{'p'} : '';
	
	# then process the input file(s)
	my $args = scalar @ARGV;
	if ( $args < 1 ) {
		process_file( 'STDIN' );
	} else {
		for( my $i = 0; $i < $args; $i++ ) {
			open(my $file, "<$ARGV[$i]") || 
				die "Unable to open input file $ARGV[$i]";
			process_file( $file );
			close( $file );
		}
	}

	# generate our report
	report();

	exit(0);
}

main();
