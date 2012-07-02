#!/usr/bin/python
import argparse
import os
import subprocess
import sys
import yaml

head = ''
clients = ''
servers = ''
mons = ''
rgws = ''

def pdsh(nodes, command):
    args = ['pdsh', '-R', 'ssh', '-w', nodes, command]
    return subprocess.Popen(args)

def pdcp(nodes, flags, localfile, remotefile):
    args = ['pdcp', '-R', 'ssh', '-w', nodes, localfile, remotefile]
    if flags:
        args = ['pdcp', '-R', 'ssh', '-w', nodes, flags, localfile, remotefile]
    return subprocess.Popen(args)

def rpdcp(nodes, flags, remotefile, localfile):
    args = ['rpdcp', '-R', 'ssh', '-w', nodes, remotefile, localfile]
    if flags:
        args = ['rpdcp', '-R', 'ssh', '-w', nodes, flags, remotefile, localfile]
    return subprocess.Popen(args)

def read_config(config_file):
    config = {}
    try:
        with file(config_file) as f:
            g = yaml.safe_load_all(f)
            for new in g:
                config.update(new)
    except IOError, e:
        raise argparse.ArgumentTypeError(str(e))
    return config

def make_remote_dir(remote_dir):
    print 'Making remote directory: %s' % remote_dir
    pdsh('%s,%s,%s,%s' % (clients,servers,mons,rgws), 'mkdir -p -m0755 -- %s' % remote_dir).communicate()

def sync_files(tmp_dir, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    rpdcp('%s,%s,%s,%s' % (clients,servers,mons,rgws), '-r', tmp_dir, out_dir).communicate()

def setup_cluster(config, tmp_dir):
    global head, clients, servers, mons, rgws, fs
    print "Setting up cluster..."
    head = config.get('head', '')
    clients = config.get('clients', '')
    rgws = config.get('rgws', '')
    servers = config.get('servers', '')
    mons = config.get('mons', '')
    fs = config.get('filesystem', 'btrfs')
    config_file = config.get('ceph.conf', '/etc/ceph/ceph.conf')

    print 'Deleting %s' % tmp_dir
    pdsh('%s,%s,%s,%s' % (clients,servers,mons,rgws), 'rm -rf %s' % tmp_dir_base).communicate()
    print "Stoping monitoring."
    stop_monitoring()
    print "Stopping ceph."
    stop_ceph()
    print "Distributing %s." % config_file
    setup_ceph_conf(config_file)
    if fs == '':
        shutdown("No OSD filesystem specified.  Exiting.")
  
    print "Building the underlying %s filesystem" % fs
    if fs == 'btrfs':
        setup_btrfs()
    elif fs == 'ext4':
        setup_ext4()
    elif fs == 'xfs':
        setup_xfs()
    else:
        shutdown('%s not recognized as a valid filesystem. Exiting.' % fs)

    print 'Running mkcephfs.'
    mkcephfs()
    print 'Purging logs.'
    purge_logs()
    print 'Starting Ceph.'
    start_ceph()
    print 'Setting up pools'
    setup_pools()
    print 'Creating rgw users.'
    setup_rgw()
    print 'Downloading s3-tests.'
    setup_s3tests(tmp_dir)

def shutdown(message):
    print "Stopping monitoring."
    stop_monitoring()
    print "Stopping ceph."
    stop_ceph()
    sys.exit(message)

def purge_logs():
    pdsh('%s,%s,%s,%s' % (clients, servers, mons, rgws), 'sudo rm -rf /var/log/ceph/*').communicate()

def make_movies(tmp_dir):
    seekwatcher = '/home/ubuntu/bin/seekwatcher'
    blktrace_dir = '%s/blktrace' % tmp_dir
    pdsh(servers, 'cd %s;%s -t device0 -o device0.mpg --movie' % (blktrace_dir,seekwatcher)).communicate()
    pdsh(servers, 'cd %s;%s -t device1 -o device1.mpg --movie' % (blktrace_dir,seekwatcher)).communicate()
    pdsh(servers, 'cd %s;%s -t device2 -o device2.mpg --movie' % (blktrace_dir,seekwatcher)).communicate()
    pdsh(servers, 'cd %s;%s -t device3 -o device3.mpg --movie' % (blktrace_dir,seekwatcher)).communicate()
    pdsh(servers, 'cd %s;%s -t device4 -o device4.mpg --movie' % (blktrace_dir,seekwatcher)).communicate()
    pdsh(servers, 'cd %s;%s -t device5 -o device5.mpg --movie' % (blktrace_dir,seekwatcher)).communicate()

def start_monitoring(tmp_dir):
    collectl_dir = '%s/collectl' % tmp_dir
    blktrace_dir = '%s/blktrace' % tmp_dir
    pdsh('%s,%s,%s,%s' % (clients, servers, mons, rgws), 'mkdir -p -m0755 -- %s;collectl -s+YZ -i 1:10 -F0 -f %s' % (collectl_dir,collectl_dir))
    pdsh(servers, 'mkdir -p -m0755 -- %s;cd %s;sudo blktrace -o device0 -d /dev/disk/by-partlabel/osd-device-0-data' % (blktrace_dir,blktrace_dir))
    pdsh(servers, 'cd %s;sudo blktrace -o device1 -d /dev/disk/by-partlabel/osd-device-1-data' % blktrace_dir)
    pdsh(servers, 'cd %s;sudo blktrace -o device2 -d /dev/disk/by-partlabel/osd-device-2-data' % blktrace_dir)
    pdsh(servers, 'cd %s;sudo blktrace -o device3 -d /dev/disk/by-partlabel/osd-device-3-data' % blktrace_dir)
    pdsh(servers, 'cd %s;sudo blktrace -o device4 -d /dev/disk/by-partlabel/osd-device-4-data' % blktrace_dir)
    pdsh(servers, 'cd %s;sudo blktrace -o device5 -d /dev/disk/by-partlabel/osd-device-5-data' % blktrace_dir)

def stop_monitoring():
    pdsh('%s,%s,%s,%s' % (clients,servers,mons,rgws), 'pkill -f collectl').communicate()
    pdsh(servers, 'sudo pkill -f blktrace').communicate()

def start_ceph():
    pdsh('%s,%s,%s,%s' % (clients,servers,mons,rgws), 'sudo /etc/init.d/ceph start').communicate()
    pdsh(rgws, 'sudo /etc/init.d/radosgw start;sudo /etc/init.d/apache2 start').communicate()

def stop_ceph():
    pdsh('%s,%s,%s,%s' % (clients,servers,mons,rgws), 'sudo /etc/init.d/ceph stop').communicate()
    pdsh(rgws, 'sudo /etc/init.d/radosgw stop;sudo /etc/init.d/apache2 stop').communicate()

def setup_ceph_conf(conf_file):
    pdcp('%s,%s,%s,%s,%s' % (head,clients,servers,mons,rgws), '', conf_file, '/tmp/ceph.conf').communicate()
    pdsh('%s,%s,%s,%s,%s' % (head,clients,servers,mons,rgws), 'sudo cp /tmp/ceph.conf /etc/ceph/ceph.conf').communicate()

def mkcephfs():
    pdsh(head, 'sudo mkcephfs -a -c /etc/ceph/ceph.conf').communicate()

def setup_btrfs():
    for device in xrange (0,6):
        pdsh(servers, 'sudo umount /srv/osd-device-%s;sudo rmdir /srv/osd-device-%s' % (device, device)).communicate()
        pdsh(servers, 'sudo mkdir /srv/osd-device-%s' % device).communicate()
        pdsh(servers, 'sudo mkfs.btrfs -l 64k -n 64k /dev/disk/by-partlabel/osd-device-%s-data' % device).communicate()
        pdsh(servers, 'sudo mount -o noatime -t btrfs /dev/disk/by-partlabel/osd-device-%s-data /srv/osd-device-%s' % (device, device)).communicate()

def setup_ext4():
    for device in xrange (0,6):
        pdsh(servers, 'sudo umount /srv/osd-device-%s;sudo rmdir /srv/osd-device-%s' % (device, device)).communicate()
        pdsh(servers, 'sudo mkdir /srv/osd-device-%s' % device).communicate()
        pdsh(servers, 'sudo mkfs.ext4 /dev/disk/by-partlabel/osd-device-%s-data' % device).communicate()
        pdsh(servers, 'sudo mount -o user_xattr,noatime -t xfs /dev/disk/by-partlabel/osd-device-%s-data /srv/osd-device-%s' % (device, device)).communicate()

def setup_xfs():
    for device in xrange (0,6):
        pdsh(servers, 'sudo umount /srv/osd-device-%s;sudo rmdir /srv/osd-device-%s' % (device, device)).communicate()
        pdsh(servers, 'sudo mkdir /srv/osd-device-%s' % device).communicate()
        pdsh(servers, 'sudo mkfs.xfs -f -d su=64k,sw=1 -i size=2048 /dev/disk/by-partlabel/osd-device-%s-data' % device).communicate()
        pdsh(servers, 'sudo mount -o noatime -t xfs /dev/disk/by-partlabel/osd-device-%s-data /srv/osd-device-%s' % (device, device)).communicate()

def setup_rgw():
    pdsh(rgws, 'sudo radosgw-admin user create --uid user --display_name user --access-key test --secret \'dGVzdA==\' --email test@test.test').communicate()
    pdsh(rgws, 'sudo radosgw-admin user create --uid user2 --display_name user2 --access-key test2 --secret \'dGVzdDI=\' --email test@test.test').communicate()

def setup_pools():
    pdsh(head, 'sudo ceph osd pool create rest-bench 4096 4096').communicate()
    pdsh(head, 'sudo ceph osd pool create rados-bench 4096 4096').communicate()
    pdsh(rgws, 'sudo radosgw-admin -p rest-bench pool add').communicate()
    pdsh(rgws, 'sudo radosgw-admin -p .rgw.buckets pool rm').communicate()

def setup_s3tests(tmp_dir):
    pdsh(clients, 'sudo apt-get update').communicate()
    pdsh(clients, 'sudo apt-get install libyaml-dev').communicate()
    pdsh(clients, 'rm -rf %s/s3-tests' % tmp_dir).communicate()
    pdsh(clients, 'mkdir -p -m0755 -- %s' % tmp_dir).communicate()
    pdsh(clients, 'git clone http://ceph.newdream.net/git/s3-tests.git %s/s3-tests' % tmp_dir).communicate()
    pdsh(clients, 'cd %s/s3-tests;./bootstrap' % tmp_dir).communicate()
    pdcp(clients, '-r', 'conf', '%s/s3-tests' % tmp_dir).communicate()

def cleanup_tests():
    pdsh(clients, 'sudo pkill -f rados; sudo pkill -f rest-bench; sudo pkill -f ceph').communicate()

def run_radosbench(config, tmp_dir, archive_dir):
    print 'Running radosbench tests...'

    time = str(config.get('time', '360'))
    pool = str(config.get('pool', ''))
    if pool: pool = '-p %s' % pool
    concurrent_ops = str(config.get('concurrent_ops', ''))
    if concurrent_ops: concurrent_ops = '-t %s' % concurrent_ops

    op_sizes = config.get('op_sizes', [])
    for op_size in op_sizes:
        run_dir = '%s/radosbench/op_size-%08d' % (tmp_dir, op_size)
        out_dir = '%s/radosbench/op_size-%08d' % (archive_dir, op_size)

        make_remote_dir(run_dir)
        out_file = '%s/output' % run_dir
        op_size = '-b %s' % op_size
        start_monitoring(run_dir)
        pdsh(clients, '/usr/bin/rados %s %s bench %s write %s > %s' % (pool, op_size, time, concurrent_ops, out_file)).communicate()
        stop_monitoring()
        make_movies(run_dir)
        sync_files('%s/*' % run_dir, out_dir)
    print 'Done.'

def run_restbench(config, tmp_dir, archive_dir):
    print 'Running rest-bench tests...'

    time = str(config.get('time', '360'))
    time = '--seconds=%s' % time
    concurrent_ops = str(config.get('concurrent_ops', ''))
    if concurrent_ops: concurrent_ops = '-t %s' % concurrent_ops
    bucket = str(config.get('bucket', ''))
    if bucket: bucket = '--bucket=%s' % bucket
    access_key = str(config.get('access_key', ''))
    if access_key: access_key = '--access-key=%s' % access_key
    secret = str(config.get('secret', ''))
    if secret: secret = '--secret=%s' % secret
    api_host = str(config.get('api_host', ''))
    if api_host: api_host = '--api-host=%s' % api_host

    op_sizes = config.get('op_sizes', [])

    for op_size in op_sizes:
        run_dir = '%s/rest-bench/op_size-%08d' % (tmp_dir, op_size)
        out_dir = '%s/rest-bench/op_size-%08d' % (archive_dir, op_size)
        make_remote_dir(run_dir)
        out_file = '%s/output' % run_dir
        op_size = '-b %s' % op_size

        start_monitoring(run_dir)
	pdsh(clients, '/usr/bin/rest-bench %s %s %s %s %s %s %s write > %s' % (api_host, access_key, secret, concurrent_ops, op_size, time, bucket, out_file)).communicate()
        stop_monitoring()
        make_movies(run_dir)
        sync_files('%s/*' % run_dir, out_dir)
    print 'Done.'


def run_s3rw(config, tmp_dir, archive_dir):
    print 'Running s3rw tests...'

    config_files = config.get('config_files', [])
    for config_file in config_files:
        short_name = config_file.rpartition('/')[2]
        run_dir = '%s/s3rw/%s' % (tmp_dir, short_name)
        out_dir = '%s/s3rw/%s' % (archive_dir, short_name)

        make_remote_dir(run_dir)
        out_file = '%s/output' % run_dir 
        start_monitoring(run_dir)
        pdsh(clients, '%s/s3-tests/virtualenv/bin/s3tests-test-readwrite < %s > %s' % (tmp_dir, config_file, out_file)).communicate()
        stop_monitoring()
        make_movies(run_dir)
        sync_files('%s/*' % run_dir, out_dir)
    print "Done."

def run_s3func(config, tmp_dir, archive_dir):
    print 'Running s3func tests...'
    
    config_files = config.get('config_files', [])
    for config_file in config_files:
        short_name = config_file.rpartition('/')[2]
        run_dir = '%s/s3func/%s' % (tmp_dir, short_name)
        out_dir = '%s/s3func/%s' % (archive_dir, short_name)

        make_remote_dir(run_dir)
        out_file = '%s/output' % run_dir 
        start_monitoring(run_dir)
        pdsh(clients, 'export S3TEST_CONF=%s;cd /tmp/cephtest/s3-tests;virtualenv/bin/nosetests -a \'!fails_on_rgw\' &> %s' % (config_file, out_file)).communicate()
        stop_monitoring()
        make_movies(run_dir)
        sync_files('%s/*' % run_dir, out_dir)
    print 'Done.'

def parse_args():
    parser = argparse.ArgumentParser(description='Continuously run ceph tests.')
    parser.add_argument(
        '--archive',
        required = True, 
        help = 'Directory where the results should be archived.',
        )
    parser.add_argument(
        'config_file',
        help = 'YAML config file.',
        )
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    ctx = parse_args()
    config = read_config(ctx.config_file)
    tmp_dir_base = '/tmp/cephtest'

    iteration = 0

    cluster_config = config.get('cluster', {})
    rb_config = config.get('radosbench', {})
    restbench_config = config.get('restbench', {})
    s3func_config = config.get('s3func', {})
    s3rw_config = config.get('s3rw', {})

    if not (cluster_config):
        shutdown('No cluster section found in config file, bailing.')
    if not (rb_config or restbench_config or s3func_config or s3rw_config):
        shutdown('No task sections found in config file, bailing.')

    setup_cluster(cluster_config, tmp_dir_base)
    while True:
        archive_dir = os.path.join(ctx.archive, '%08d' % iteration)
        if os.path.exists(archive_dir):
            print 'Skipping existing iteration %d.' % iteration
            next
        os.makedirs(archive_dir)

        print "Running iteration: %d" % iteration
        print "Cleaning up tests..."
        cleanup_tests()
        tmp_dir = '%s/%08d' % (tmp_dir_base, iteration)
        if rb_config:
            run_radosbench(rb_config, tmp_dir, archive_dir)
        if restbench_config:
            run_restbench(restbench_config, tmp_dir, archive_dir)
        if s3func_config:
            run_s3func(s3func_config, tmp_dir, archive_dir)
        if s3rw_config:
            run_s3rw(s3rw_config, tmp_dir, archive_dir)       

        iteration += 1
