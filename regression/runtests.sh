#!/bin/bash
#HOME="/home/regression"
#VERSIONS=( "firefly" "giant" "master")
VERSIONS=( "firefly" "master" )
UPGRADE_CMD="$HOME/bin/upgrade-ceph.sh"
CONFDIR=$1
CBT="$HOME/src/ceph-tools/cbt/cbt.py"
DATE=`date +%Y%m%d`

for VERSION in "${VERSIONS[@]}"
do
  # Upgrade Ceph
  $UPGRADE_CMD reg $VERSION

  # Run Tests
  for SUITE in $( find $CONFDIR/*/ -type d -exec basename {} \;)
  do
    for TEST in $( find $CONFDIR/$SUITE/*.yaml -type f -exec basename {} \; | cut -d"." -f 2)
    do
      CBTCONF="$CONFDIR/$SUITE/runtests.$TEST.yaml"
      ARCHIVE="/$HOME/data/$DATE/$VERSION/$SUITE/$TEST"
      mkdir -p $ARCHIVE
      $CBT --archive $ARCHIVE $CBTCONF 2>&1 | tee $ARCHIVE/cbt.out
    done
  done
done
