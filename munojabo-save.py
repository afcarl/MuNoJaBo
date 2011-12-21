#!/usr/bin/env python3

import sys, time, argparse, configparser
from munin import *
from munin.sql import mysql, sqlite

# config-file
config = configparser.ConfigParser(common.defaults)
config.read('/etc/munojabo.conf')

parser = argparse.ArgumentParser(version='1.0')
group = parser.add_argument_group("Required options")
group.add_argument('--host', help='The host these warnings are for')
group.add_argument('--graph', help='The graph that has a warning/critical condition. This is the same'
    ' as the graph_title of the munin-plugin.')

parser.add_argument('--critical', help='Fields with a "critical" value.')
parser.add_argument('--warning', help='Fields with a "warning" value.')
parser.add_argument('--unknown', help='Fields with a "unknown" value.')
args = parser.parse_args()

if not args.critical and not args.warning and not args.unknown:
    sys.exit(0) # called with nothing to report.

# create SQL backend:
backend = config.get('sql', 'backend')
if  backend == 'sqlite':
    sql = sqlite(args, config)
elif backend == 'mysql':
    sql = mysql(args, config)
else:
    raise RuntimeError("Invalid SQL backend specified.")
    
def handle_fields( raw_fields, cond ):
    raw_fields = raw_fields.split( ";" )

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