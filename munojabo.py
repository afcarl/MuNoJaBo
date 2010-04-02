#!/usr/bin/python -Wignore

"""
munojabo.py is a simple jabber-bot designed to be called by munin[1] if any
values are not within the configured safe margins. Please see the README for
documentation on how to configure munin to use this script. This script was
written by Mathias Ertl <mati@fsinf.at>.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

[1] http://munin.projects.linpro.no/
"""

import sys, xmpp, time, ConfigParser, MySQLdb
from optparse import OptionParser, OptionGroup
from munin import *

log_file = '/var/log/munojabo.log'

# config-file
config = ConfigParser.ConfigParser({ 
	'debug': 'False',
	'user': 'munojabo',
	'db': 'munojabo',
	'host': 'localhost'
	})
config.read( '/etc/munojabo.conf' )

parser = OptionParser( version='1.0' )
group = OptionGroup( parser, "Required options" )
group.add_option( '--jid', help='The JID to send the warnings to.' )
group.add_option( '--host', help='The host these warnings are for' )
group.add_option( '--graph', help='The graph that has a warning/critical '
	'condition. This is the same as the graph_title of the munin-plugin.' )
parser.add_option_group( group )

parser.add_option( '--critical', help='Fields with a "critical" value.' )
parser.add_option( '--warning', help='Fields with a "warning" value.' )
parser.add_option( '--unknown', help='Fields with a "unknown" value.' )
parser.add_option( '--clean', action='store_true', default=False,
	help='Clean notifications older than 21600 secondes.' )
parser.add_option( '--force-send', action='store_true', default=False,
	help='Send message no matter what.' )
parser.add_option( '--debug', action='store_true', default=False,
	help='Also print output to stdout' )
(options, args) = parser.parse_args()

def get_stamp( secs ):
	return time.strftime( '%Y-%m-%d %H:%M:%S', time.gmtime( time.time() - secs ) )

def log( message ):
	stamp = str(time.strftime( '%Y-%m-%d %H:%M:%S' ))
	fi = open( log_file, 'a' )
	fi.write( stamp + ": " + message + "\n" )
	fi.close()
	if options.debug:
		print( message.strip() )

log( str( sys.argv[1:] ) )

# connect to mysql database:
mysql_conn = MySQLdb.connect(
	host=config.get( 'mysql', 'host' ),
	user=config.get( 'mysql', 'user' ),
	passwd=config.get( 'mysql', 'pass' ),
	db=config.get( 'mysql', 'db' )
	)
mysql_cursor = mysql_conn.cursor()

# handle the --clean option:
if options.clean == True:
	stamp = get_stamp( 21600 )
	mysql_cursor.execute( "DELETE FROM alerts WHERE stamp < %s", (stamp) )
	mysql_cursor.close()
	mysql_conn.commit()
	mysql_conn.close()
	sys.exit( 0 )

# see if all required options (jid, host, graph) were given:
if not (options.jid and options.host and options.graph):
	parser.print_help()
	sys.exit(1)

# build subject and text:
subj = "Munin notification for %s" %(options.host)
text = "One or more fields on graph %s on %s are in warning or critical range.\n" %(options.graph, options.host)

def handle_fields( raw_fields, cond ):
	raw_fields = raw_fields.split( ";" )
	fields = []
	stamp = get_stamp( 21600 )

	for raw_field in raw_fields:
		f = field.field( raw_field )
		mysql_cursor.execute( "SELECT * FROM alerts WHERE stamp > %s AND host=%s AND graph=%s AND field=%s AND cond=%s", 
			(stamp, options.host, options.graph, f.fieldname, cond) )
		row = mysql_cursor.fetchone()
		
		if row == None:
			fields.append( f )
			mysql_cursor.execute( """INSERT INTO alerts(host, graph, field, cond) VALUES (%s, %s, %s, %s)""",
				(options.host, options.graph, f.fieldname, cond) )
	return fields
	
def add_fields( text, fields ):
	ret = "\n%s:\n" %(text.capitalize())
	for f in fields:
		ret += "%s\n" % (f)
	return ret

# credentials for the bot
user = config.get( 'xmpp', 'user' )
server = config.get( 'xmpp', 'server' )
resource = config.get( 'xmpp', 'resource' )
password = config.get( 'xmpp', 'pass' )

# connect to and authenticate with jabber-server:
cl = xmpp.Client( server, debug = [] )
cl.connect()
if cl.connected == '':
	raise RuntimeError( 'Could not connect to jabber server', server )
auth = cl.auth( user, password, resource )
if auth == None:
	raise RuntimeError( 'Could not authenticate %s@%s' %(user, server) )

# parse critical fields
if options.critical:
	options.critical = handle_fields( options.critical, "critical" )
if options.warning:
	options.warning = handle_fields( options.warning, "warning" )
if options.unknown:
	options.unknown = handle_fields( options.unknown, "unknown" )

# sometimes we do get called with nothing to report, this option also triggers
# when this has been reported already.
if not options.critical and not options.warning and not options.unknown \
		and not options.force_send:
	log( "Called with nothing to report." )
	sys.exit(0)

if options.critical and len(options.critical) > 0:
	text += add_fields( "Critical", options.critical )
if options.warning and len(options.warning) > 0:
	text += add_fields( "Warning", options.warning )
if options.unknown and len(options.unknown) > 0:
	text += add_fields( "Unknown", options.unknown )

# Actually send the message via jabber:
cl.send( xmpp.protocol.Message( options.jid, text, subject=subj ) )

# cleanup
mysql_cursor.close()
mysql_conn.commit()
mysql_conn.close()
cl.disconnect()
