#!/usr/bin/env python3

"""This file is part of munojabo.

munojabo-save.py is a simple script designed to be called by munin[1] if any monitored values are
outside safe limits. Please see the README for documentation on how to configure munin to use this
script. This script was written by Mathias Ertl <mati@fsinf.at>.

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
from munin import field
from munin.sql import mysql
from munin.sql import sqlite

# config-file
config = configparser.ConfigParser(common.defaults)
config.read('/etc/munojabo.conf')

parser = argparse.ArgumentParser()
group = parser.add_argument_group("Required options")
group.add_argument('--host', help='The host these warnings are for')
group.add_argument('--graph', help='The graph that has a warning/critical condition. This is the '
                   'same as the graph_title of the munin-plugin.')

parser.add_argument('--version', action='version', version='%(prog)s 2.0')
parser.add_argument('--critical', help='Fields with a "critical" value.')
parser.add_argument('--warning', help='Fields with a "warning" value.')
parser.add_argument('--unknown', help='Fields with a "unknown" value.')
args = parser.parse_args()

if not args.critical and not args.warning and not args.unknown:
    sys.exit(0)  # called with nothing to report.

# create SQL backend:
backend = config.get('sql', 'backend')
if backend == 'sqlite':
    sql = sqlite(args, config)
elif backend == 'mysql':
    sql = mysql(args, config)
else:
    raise RuntimeError("Invalid SQL backend specified.")


def handle_fields(raw_fields, cond):
    raw_fields = raw_fields.split(";")

    for raw_field in raw_fields:
        f = field.field(raw_field)
        sql.insert_alert(args.host, args.graph, cond, f)

# parse critical fields
if args.critical:
    handle_fields(args.critical, "critical")
if args.warning:
    handle_fields(args.warning, "warning")
if args.unknown:
    handle_fields(args.unknown, "unknown")

sql.close()
