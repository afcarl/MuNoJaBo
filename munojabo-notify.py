#!/usr/bin/env python3

"""
This file is part of munojabo.

munojabo-notify.py is a script that reads alerts saved by munojabo-save.py and sends
jabber-notifications to the configured jabber accounts. Please see the README for documentation on
how to configure munin to use this script.  This script was written by Mathias Ertl
<mati@fsinf.at>.

munojabo is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not,
see <http://www.gnu.org/licenses/>.

[1] http://munin.projects.linpro.no/
"""

import argparse
import configparser
import sys

from munin import common
from munin.sql import mysql
from munin.sql import sqlite
from munin.xmpp import MuNoJaBoConnection

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

# config-file
config = configparser.ConfigParser(common.defaults)
config.read('/etc/munojabo.conf')

parser = argparse.ArgumentParser()
parser.add_argument('--run-freq', metavar='SECS', default=300, type=int,
                    help="This script is run every SECS seconds.")
parser.add_argument('--notification-freq', metavar='SECS', default=21600, type=int,
                    help="This script will send notifications again after SECS seconds.")
parser.add_argument('--force-send', action='store_true', default=False,
                    help='Send message no matter what.')
parser.add_argument('--debug', action='store_true', default=False,
                    help='Also print output to stdout')
parser.add_argument('--version', action='version', version='%(prog)s 2.0')
args = parser.parse_args()

# create SQL backend:
backend = config.get('sql', 'backend')
if backend == 'sqlite':
    sql = sqlite(args, config)
elif backend == 'mysql':
    sql = mysql(args, config)
else:
    raise RuntimeError("Invalid SQL backend specified.")

notifications = {}
alerts = sql.get_alerts()
for host, graph_data in alerts.items():
    if not config.has_option('hosts', host):
        continue

    jids = [jid.strip(', ') for jid in config.get('hosts', host).split(' ')]
    for jid in jids:
        if jid not in notifications:
            notifications[jid] = {}
        if host not in notifications[jid]:
            notifications[jid][host] = {}

        for graph, fields in graph_data.items():
            notifications[jid][host][graph] = fields

if notifications:
    cl = MuNoJaBoConnection(config, notifications)
    if cl.connect():
        cl.process(block=True)

# cleanup
sql.clean()  # clean old alerts
sql.close()
