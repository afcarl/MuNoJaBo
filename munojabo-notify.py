#!/usr/bin/env python3

import sys, argparse, configparser, thread
from munin import *
from munin.sql import mysql, sqlite

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
    
# config-file
config = configparser.ConfigParser(common.defaults)
config.read('/etc/munojabo.conf')

parser = argparse.ArgumentParser(version='1.0')
parser.add_argument('--run-freq', metavar='SECS', default=300, type=int,
    help="This script is run every SECS seconds.")
parser.add_argument('--notification-freq', metavar='SECS', default=21600, type=int,
    help="This script will send notifications again after SECS seconds.")
parser.add_argument('--clean', action='store_true', default=False,
    help='Clean notifications older than 21600 secondes.')
parser.add_argument('--force-send', action='store_true', default=False,
    help='Send message no matter what.')
parser.add_argument('--debug', action='store_true', default=False,
    help='Also print output to stdout')
args = parser.parse_args()

# create SQL backend:
backend = config.get('sql', 'backend')
if  backend == 'sqlite':
    sql = sqlite(args, config)
elif backend == 'mysql':
    sql = mysql(args, config)
else:
    raise RuntimeError("Invalid SQL backend specified.")
    
# handle the --clean option:
if args.clean == True:
	sql.clean()
	sql.close()
	sys.exit(0)
	
notifications = {}
alerts = sql.get_alerts()
for host, graph_data in alerts.iteritems():
    if not config.has_option('hosts', host):
        continue
    
    jids = [jid.strip(', ') for jid in config.get('hosts', host).split(' ')]
    for jid in jids:
        if jid not in notifications:
            notifications[jid] = {}
        if host not in notifications[jid]:
            notifications[jid][host] = {}
    
        for graph, fields in graph_data.iteritems():
            notifications[jid][host][graph] = fields

if notifications:
    cl = xmpp.MuNoJaBoConnection(config, notifications)
    if cl.connect():
    	cl.process(block=True)

# cleanup
sql.close()