#!/bin/bash

./runtests.py --archive=/data/8spinning-8proc-dc/SAS2208-r0x8-bobtail/btrfs/ runtests.btrfs.yaml
./runtests.py --archive=/data/8spinning-8proc-dc/SAS2208-r0x8-bobtail/xfs/ runtests.xfs.yaml
./runtests.py --archive=/data/8spinning-8proc-dc/SAS2208-r0x8-bobtail/ext4/ runtests.ext4.yaml

