#!/usr/bin/perl
#
# script: bugmunch
#	
# purpose:
#	to read through a raw bug list and generate
#	over-time arrival/dispatch statistics.
#
# output:
#	one row per reporting period, with a date
#	and arrival/dispatch/backlog #s for that period
#
# TODO:
#	1. get tracker types and priorities from redmine
#	   (or at least from a configuration file).  It
#	   appears 'lc variable' and 'y:x:colorcol' will
#	   let me control the color from the data.
#	2. can I get gnuplot to compute the cumulatives
#	   (which are merely the rolling sum of new-fix)
#
use warnings;
use strict;
use Carp;

use Getopt::Std;
use File::Basename;
use Time::Local;

use Bugparse;

sub usage()
{	
	print STDERR "Usage: bugmunch.pl [switches] [file ...]\n";
	print STDERR "        -m ......... monthly accumulation\n";
	print STDERR "        -w ......... weekly accumulation\n";
	print STDERR "        -r ......... report (vs data)\n";
	print STDERR "        -s date .... report start date\n";
	print STDERR "        -e date .... report end date\n";
	print STDERR "        -p prefix .. prefix for output file names\n";
}

# parameters
my $report_period = 'm';# weekly or monthly
my $report_fmt = 'd';	# data vs report
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
my $period_start = 0;		# date of current accumulation period
my %period_counts = ();		# counts by type for current period
my %cumulative_counts = ();	# net accumulated counts, by type
my %fixes = ();			# counts by type of (future) fixes 
my $period_total = 0;		# total count for current period

#
# routine:	process_flush
#
# purpose:	flush out all operations up to 
# 		(but not including) specified date
#
# Note: we have to incrementatlly work our way up to the specified
# 	date because there may be future bug fixes queued up for
# 	intervals during which no bugs were filed, and we want
# 	to make sure that we hit those intervals so that we can
# 	flush out the fix counts.
#
#	We do all of our time computations in GMT (rather than local),
#	because it eliminates Daylight Savings Time bumps.  This has
#	no effect on the output because we only use the binary
#	representation to measure intervals.
#
sub process_flush
{
	(my $upto) = ($_[0]);

	# on the first call, just print a header and zero all counters
	if ($period_start == 0) {
		# initialize all the counters
		$period_start = $upto;
		$period_total = 0;
		for ( my $i = 0; $i < scalar @columns; $i++ ) {
			$period_counts{$columns[$i]} = 0;
			$cumulative_counts{$columns[$i]} = 0;
		}

		if ($report_fmt ne 'r') {
			# print out the headers
			printf( "# date " );
			for ( my $i = 0; $i < scalar @columns; $i++ ) {
				printf( "new-%s ", $columns[$i] );
			}
			for ( my $i = 0; $i < scalar @columns; $i++ ) {
				printf( "fix-%s ", $columns[$i] );
			}
			printf("\n");
		}
		return;
	}

	# generate output for all periods between now and up-to
	while( $period_start < $upto ) {
		# print out the report for this period
		my ($s, $m, $h, $mday, $mon, $year, $wd, $yd, $dst) = gmtime( $period_start );
		my $date = sprintf("%02d/%02d/%04d", $mon+1, $mday, $year+1900);

		# see if we have any new bugs to report
		if ($period_start >= $start_date &&
		    $period_start <= $end_date &&
		    ($period_total > 0 || defined( $fixes{$period_start}))) {
			if ($report_fmt eq 'r') {
				printf( "%-16s      %7s  %7s %7s\n", $date, "new", "fixed", "remain" );
				for( my $i = 0; $i < scalar @columns; $i++ ) {
					printf( "    %-16s ", $columns[$i] );
					printf( " %7d ", $period_counts{ $columns[$i] });
					$cumulative_counts{$columns[$i]} += $period_counts{ $columns[$i] };
					if (defined( $fixes{$period_start})) {
						printf( " %7d", $fixes{ "$period_start-$columns[$i]" });
						$cumulative_counts{$columns[$i]} -= $fixes{ "$period_start-$columns[$i]" };
					} else {
						printf( " %7d", 0 );
					}
					printf( " %7d", $cumulative_counts{ $columns[$i] });
					printf( "\n" );
				}
				printf( "\n" );
			} else {
				# report the bugs opened during this period
				printf( "%s ", $date );
				for ( my $i = 0; $i < scalar @columns; $i++ ) {
					printf( "%d ", $period_counts{ $columns[$i] });
					$cumulative_counts{$columns[$i]} += $period_counts{ $columns[$i] };
				}

				# report the bugs fixed during this period
				for ( my $i = 0; $i < scalar @columns; $i++ ) {
					if (defined( $fixes{$period_start})) {
						printf( "%d ", $fixes{ "$period_start-$columns[$i]" });
						$cumulative_counts{$columns[$i]} -= $fixes{ "$period_start-$columns[$i]" };
					} else {
						printf( "0 " );
					}
				}

				# report the cumulative totals as of this period
				for ( my $i = 0; $i < scalar @columns; $i++ ) {
					printf( "%d ", $cumulative_counts{ $columns[$i] });
				}

				printf( "\n" );
			}
		} else { # otherwise, just update the cumulative counts
			for ( my $i = 0; $i < scalar @columns; $i++ ) {
				$cumulative_counts{$columns[$i]} += $period_counts{ $columns[$i] };
				if (defined( $fixes{$period_start})) {
					$cumulative_counts{$columns[$i]} -= $fixes{ "$period_start-$columns[$i]" };
				} 
			}
		}

		# and reset the reporting period
		$period_total = 0;
		for ( my $i = 0; $i < scalar @columns; $i++ ) {
			$period_counts{$columns[$i]} = 0;
			if (defined( $fixes{$period_start})) {
				delete $fixes{"$period_start-$columns[$i]"};
			}
		}

		# advance to the next reporting period
		if ($report_period eq "m") { 	# next month
			if ($mon == 11) {
				$period_start = timegm(0, 0, 0, 1, 0, $year+1901);
			} else {
				$period_start = timegm(0, 0, 0, 1, $mon+1, $year+1900);
			}
		} else {	# next week
			$period_start += (7 * 24 * 60 * 60);
		}
	}
}

# return the number of days in a time interval
sub days
{	(my $t) = ($_[0]);

	return ($t / (24 * 60 * 60));
}

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
# 		(based on the "report_period" parameter)
#
sub get_period
{
	# discect the specified time
	(my $mon, my $day, my $year) = split( '/', $_[0] );

	# months: fall back to the first of that month
	if ($report_period eq 'm') {
		return timegm( 0, 0, 0, 1, $mon-1, $year );
	} else {	# days: fall back to sunday of that week
		my $when = timegm( 0, 0, 0, $day, $mon-1, $year );
		my ($s, $m, $h, $md, $mn, $yr, $wd, $yd, $dst) = gmtime( $when );
		$when -= $wd * 24 * 60 * 60;
		return $when;
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
	(my $created, my $bugtype, my $priority, my $fixed) = ($_[0], $_[1], $_[2], $_[3]);

	# figure out if we are in a new time period
	my $this_period = get_period( $created );
	if ($this_period != $period_start) {
		process_flush($this_period);
	}

	# accumulate the bugs filed during this period
	my $bucketname = get_bucket_name( $bugtype, $priority );
	$period_total++;
	$period_counts{$bucketname}++;

	# also note the (eventual) fix of this bug
	if ($fixed ne "none") {
		$this_period = get_period( $fixed );
		if (defined($fixes{$this_period})) {
			$fixes{$this_period}++;
		} else { # initialize the counters for this period
			$fixes{$this_period} = 1;
			for ( my $i = 0; $i < scalar @columns; $i++ ) {
				$fixes{"$this_period-$columns[$i]"} = 0;
			}
		}

		$fixes{"$this_period-$bucketname"}++;
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
	foreach my $c ('created','priority','type','closed') {
		if (!defined( $columns{$c})) {
			die("Unable to find column: $c\n");
		}
	} 
	my $crt = $columns{'created'};
	my $prt = $columns{'priority'};
	my $typ = $columns{'type'};
	my $cls = $columns{'closed'};

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
			process_newbug( $fields[$crt], $fields[$typ], $fields[$prt], $fields[$cls]);
		}
	}

	# flush out anything that might should happen in the next reporting period
	process_flush( $period_start + (31 * 24 * 60 * 60));
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
	if (!getopts('wmrs:e:p:', \%options)) {
		usage();
		exit(1);
	}

	# see what our aggregation interval is
	if (defined( $options{'m'} )) {
		$report_period = 'm';
	} elsif (defined( $options{'w'} )) {
		$report_period = 'w';
	} 
	if (defined( $options{'r'} )) {
		$report_fmt = 'r';
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

	exit(0);
}

main();
