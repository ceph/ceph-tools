#!/usr/bin/perl
#
my $usage = "usage: redmine_dump database\n";

#
# Go to the MySQL database behind a Redmine bug system, and dump
# out a record for each bug, containing information that can be
# used to generate historical statistics reports not directly 
# supported by Redmine.
#
# Perhaps if I were a better person I would have implemented the
# reports I wanted as Redmine plug-ins, but I was finding Redmine
# difficult to dance with, and once we have this information out
# we can do anything we want with it.
#	 
# Note:
#	Clearly this script knows a lot about the schemas and table
#	relationships within a Redmine database ... and some of this
#	knowledge may turn out to be specific to the cephtracker 
#	database I started with.

use warnings;
use strict;
use Carp;

use Ndn::Dreamhost::Mysql;

# Output format
my $output="# bugid\tcategory\tissue type\tsource  \tprty\tversion\tcreated \tclosed   \thistory\tstatus\n";
my $dashes="# -----\t--------\t----------\t------  \t----\t-------\t------- \t------   \t-------\t------\n";

#
# translate a mysql time/date into a more traditional date
#
sub sqldate {
	my @date = split(' ', $_[0]);
	(my $year, my $month, my $day) = split('-',$date[0]);
	return "$month/$day/$year";
}

# figure out what dabase we are using and open a connection to it
if (scalar @ARGV != 1) {
	print STDERR $usage;
	exit( 1 );
}
my $dbase = $ARGV[0];
my $db = Ndn::Dreamhost::Mysql->LoadOrDie({db_name => $dbase, dh_id => 'dh'});
my $Service = $db->Service;
my $dbh = $Service->_connect_admin;
$dbh->do("use $dbase");

# Drop-down menu values in a Redmine bug come from other tables,
# and are represented in the issue as indexes into those other
# tables.  Rather than do massive joins, I chose to simply read
# in those maps and interpret the values here ... giving me the
# opportunity to do some slightly more clever processing of the
# reports.

# buid up the issue categories map
my %categories = ('NULL'=>'none');
my $sth=$dbh->prepare("select id,name from issue_categories;");
$sth->execute();
while ( my @ref = $sth->fetchrow_array() ) {
	$categories{$ref[0]} = $ref[1];
}

# buid up the versions map
my %versions = ('NULL'=>'none');
$sth=$dbh->prepare("select id,name from versions;");
$sth->execute();
while ( my @ref = $sth->fetchrow_array() ) {
	$versions{$ref[0]} = $ref[1];
}

# buid up the priorities map
my %priorities = ('NULL'=>'none');
$sth=$dbh->prepare("select id,name from enumerations;");
$sth->execute();
while ( my @ref = $sth->fetchrow_array() ) {
	$priorities{$ref[0]} = $ref[1];
}

# build up the issue status map
my %statuses = ('NULL'=>'none');
my %is_closed = ('NULL'=>0);
$sth=$dbh->prepare("select id,name,is_closed from issue_statuses;");
while ( my @ref = $sth->fetchrow_array() ) {
	$statuses{$ref[0]} = $ref[1];
	$is_closed{$ref[0]} = $ref[2];
}

my %closures = ('NULL'=>'none');
#
# build up the bug-fixed-on map
#
#	This information is not in the issues table, so we must
#	consult the journal_details and journals tables to find
#	the last/latest status change from open to closed.
#
my $fields = 'journalized_id,old_value,value,created_on';
my $tables = 'journals,journal_details';
my $join   = 'journal_details.journal_id=journals.id and prop_key="status_id"';
my $order  = 'journal_details.id';
$sth=$dbh->prepare("select $fields from $tables where $join order by $order;");
$sth->execute();
while ( my @ref = $sth->fetchrow_array() ) 
{	if (!$is_closed{ $ref[1] } && $is_closed{ $ref[2] }) {
		$closures{$ref[0]} = sqldate($ref[3]);
	}
}

my %sources = ('NULL'=>'none');
#
# build up the list of sources map
#
#	This is not only not in the issues table, but is a
#	custom field (not likely to be present in most databases).  
# 	both of these reasons it is much easier to deal with them 
#	in a separate lookup than to include them in the main query.
#
#	If the field is not in the database or bugs do not have
#	values for the custom field, this query will simply come
#	back empty, and there will be no source map entry for those bugs.
#
$fields = 'customized_id,value';
$tables = 'custom_values,custom_fields';
$join   = 'custom_field_id=custom_fields.id and name="Source"';
$sth=$dbh->prepare("select $fields from $tables where $join;");
$sth->execute();
while ( my @ref = $sth->fetchrow_array() ) 
{	$sources{$ref[0]} = $ref[1];
}

#
# build up the version history
#
#

# print out the headings
print $output;
print $dashes;

# dump out the interesting information from each issue
$fields = 'issues.id,created_on,priority_id,fixed_version_id,category_id,status_id,trackers.name';
$tables = 'issues,trackers';
$join   = 'tracker_id=trackers.id';
$order  = 'issues.id';
$sth=$dbh->prepare("select $fields from $tables where $join order by $order;");
$sth->execute();
while ( my @ref = $sth->fetchrow_array() )
{	# we assume that all bugs have a bugid and created field
	my $bugid	= $ref[0];
	my $created	= sqldate($ref[1]);

	# many of the other fields, may be empty
	my $priority	= defined($ref[2]) ? $priorities{$ref[2]} : 'none';
	my $vers	= defined($ref[3]) ? $versions{$ref[3]} : 'none';
	my $category	= defined($ref[4]) ? $categories{$ref[4]} : 'none';
	   $category	= sprintf("%-14s", $category);	# these get long
	my $status	= defined($ref[5]) ? $statuses{$ref[5]} : 'none';
	my $tracker	= sprintf("%-14s", $ref[6]);	# these get long

	# bug source is a custom field that we look up in a map
	my $source	= 'none    ';
	if (defined( $sources{$bugid} )) {
		$source = $sources{$bugid};
		delete $sources{$bugid};
	}

	# we have to consult the status map to see if a bug is closed,
	# and then we have to look a a separate map to figure out when
	my $closed	= 'none    ';
	if ($is_closed{$ref[5]}) {
		if (defined( $closures{$bugid} )) {
			$closed = $closures{$bugid};
			delete $closures{$bugid};
		} else { # this bug was apparently created resolved!
			$closed = $created;
		}
	}

	# figuring out the version history is another whole lookup problem
	my $history	= 'none';

	# output the report we have
	print "$bugid\t$category\t$tracker\t$source\t$priority\t$vers\t$created\t$closed\t$history\t$status\n";
}
