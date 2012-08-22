#!/usr/bin/perl
#
# script: progress
#	
# purpose:
#	to read through an issue status list, pull out
#	issues with specified tags, and generate
#	per-project done and backlog sizes (tasks and points).
#
# output: (for now)
#	one row per reporting period per project
#	date project total-tasks total-points done-tasks done-points
#
use warnings;
use strict;
use Carp;

use Getopt::Std;
use File::Basename;
use Time::Local;

use Bugparse;

use constant { true => 1, false => 0 };

sub usage()
{	
	print STDERR "Usage: progress.pl [switches] [file ...]\n";
	print STDERR "        -t ......... tags to be reported\n";
	print STDERR "        -s date .... report start date\n";
	print STDERR "        -e date .... report end date\n";
	print STDERR "        -p prefix .. prefix for output file names\n";
}

# parameters
my $prefix;		# output file prefix
my $start_date;		# report starting date
my $end_date;		# report end date
my @tag_list;		# tags to be reported

# accumulated information
my %projects;
my %proj_points_todo;
my %proj_tasks_todo;
my %proj_points_done;
my %proj_tasks_done;

my $points_todo = 0;
my $points_done = 0;
my $tasks_todo = 0;
my $tasks_done = 0;

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
# routine:	flush_report
#
# purpose:	flush out the accumuated statistics
#
sub flush_report
{
	(my $sec, my $min, my $hour, my $d, my $m, my $y, my $wd, my $yd, my $dst) = localtime($end_date);
	$m += 1;
	$y += 1900;

	print "# date      \ttasks\tdone\tpoints\tdone\tsprint\n";
	print "# ----      \t-----\t----\t------\t----\t------\n";
	printf "%02d/%02d/%04d", $m, $d, $y;
	print "\t$tasks_todo\t$tasks_done\t$points_todo\t$points_done\tsprint\n";

#	print "# date      \ttasks\tdone\tpoints\tdone\tsprint\tproject\n";
#	print "# ----      \t-----\t----\t------\t----\t------\t-------\n";
#	foreach my $proj (keys %projects) {
#		my $tasks_todo = defined( $proj_tasks_todo{$proj} ) ? $proj_tasks_todo{$proj} : 0;
#		my $tasks_done = defined( $proj_tasks_done{$proj} ) ? $proj_tasks_done{$proj} : 0;
#		my $points_todo =  defined( $proj_points_todo{$proj} ) ? $proj_points_todo{$proj} : 0;
#		my $points_done = defined( $proj_points_done{$proj} ) ? $proj_points_done{$proj} : 0;
#
#		printf "%02d/%02d/%04d", $m, $d, $y;
#		print "\t$tasks_todo\t$tasks_done\t$points_todo\t$points_done\tsprint\t$proj\n";
#	}
}

#
# routine:	process_newbug
#
# purpose:	
# 	accumulate another bug report
#
sub process_newbug
{	
	(my $tag, my $project, my $closed, my $points) = ($_[0], $_[1], $_[2], $_[3]);

	if (!defined( $projects{$project} )) {
		$projects{$project} = true;
		$proj_points_todo{$project} = 0;
		$proj_points_done{$project} = 0;
		$proj_tasks_todo{$project} = 0;
		$proj_tasks_done{$project} = 0;
	}

	if ($closed eq 'none') {
		$proj_points_todo{$project} = $proj_points_todo{$project} + $points;
		$points_todo += $points;
		$proj_tasks_todo{$project} = $proj_tasks_todo{$project} + 1;
		$tasks_todo++;
	} else {
		$proj_points_done{$project} = $proj_points_done{$project} + $points;
		$points_done += $points;
		$proj_tasks_done{$project} = $proj_tasks_done{$project} + 1;
		$tasks_done++;
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
	foreach my $c ('tags', 'project', 'closed', 'points') {
		if (!defined( $columns{$c})) {
			die("Unable to find column: $c\n");
		}
	} 
	my $tag = $columns{'tags'};
	my $prj = $columns{'project'};
	my $cls = $columns{'closed'};
	my $pts = $columns{'points'};

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

			# see if it contains a requested tag
			my $good_tag = false;
			for( my $i = 0; $i < scalar @tag_list; $i++ ) {
				if (index( $fields[$tag], $tag_list[$i] ) != -1) {
					$good_tag = true;
				}
			}

			# and process the fields we care about
			if ($good_tag) {
				process_newbug( $fields[$tag], $fields[$prj], $fields[$cls], $fields[$pts]);
			}
		}
	}

	flush_report();
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
	if (!getopts('s:e:p:t:', \%options)) {
		usage();
		exit(1);
	}

	# see what tag we are extracting
	if (defined($options{'t'})) {
		my $list = $options{'t'};
		@tag_list = split(',',$list);
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
