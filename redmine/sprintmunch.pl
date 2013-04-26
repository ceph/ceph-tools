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

use Bugparse;

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
	foreach my $ver (sort keys %versions) {
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
# routine:	process_file
#
# purpose:	
# 	to read the lines of an input file and pass the non-comments
# 	to the appropriate accumulation routines.
#
# expected input: lines containing at least ...
# 	a type, priority, create date and close date
#
sub process_file
{	(my $file) = ($_[0]);

	# first line should be a headers comment
	my $first = <$file>;
	my %columns = Bugparse::parser($first);

	# make sure we got all the columns we needed
	foreach my $c ('created','priority','type','closed','version','history') {
		if (!defined( $columns{$c})) {
			die("Unable to find column: $c\n");
		}
	} 
	my $crt = $columns{'created'};
	my $prt = $columns{'priority'};
	my $typ = $columns{'type'};
	my $cls = $columns{'closed'};
	my $ver = $columns{'version'};
	my $hst = $columns{'history'};

	# use those columns to find what we want in the following lines
	while( <$file> ) {
		if (!/^#/) {	# ignore comments
			# carve it into tab separated fields
			my @fields = split( '\t', $_ );
			
			# remove any leading or trailing blanks
			for ( my $i = 0; $i < scalar @fields; $i++ ) {
				$fields[$i] =~ s/^\s+//;
				$fields[$i] =~ s/\s+$//;
			}

			# and process the fields we care about
			process_newbug( $fields[$crt], $fields[$typ], $fields[$prt], 
					$fields[$cls], $fields[$ver], $fields[$hst]);
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
