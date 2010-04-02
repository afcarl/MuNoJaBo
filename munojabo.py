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

# set to True for debugging:
log_file = '/var/log/munojabo.log'

# config-file
config = ConfigParser.ConfigParser({ 
	'debug': 'False',
	'user': 'munojabo',
	'db': 'munojabo',
	'host': 'localhost'
	})
config.read( '/etc/munojabo.conf' )

# The "general" section is optional:
if config.has_section( 'general' ):
	debug = config.getboolean( 'general', 'debug' )
else:
	debug = False

def log( message ):
	print(message)
	if debug:
		stamp = str(time.strftime( '%Y-%m-%d %H:%M:%S' ))
		fi = open( log_file, 'a' )
		fi.write( stamp + ": " + message + "\n" )
		fi.close()

log( str( sys.argv[1:] ) )

def usage( exitcode = 1 ):
	print( "Please see the README-file for documentation on how to use this script." )
	sys.exit( exitcode )

def get_stamp( secs ):
	return time.strftime( '%Y-%m-%d %H:%M:%S', time.gmtime( time.time() - secs ) )

class range():
	"""A range object is a warning/critical range as configured by munin. It
	might have an upper and a lower bound or only one of each. Here are
	three examples of valid ranges: 10:20, 10:, :20.
	
	Note that a range may be non-existent (e.g. if no warning range is
	given.)"""

	def __init__( self, text ):
		self.lower = None
		self.upper = None

		if text == "" or text == ":":
			return

		text.index( ':' ) # safety check.
		
		if text.startswith( ':' ): # only an upper bound
			self.upper = float( text[1:] )
		elif text.endswith( ':' ): # only a lower bound
			self.lower = float( text[:text.find(':')] )
		else:
			lower, upper = text.split(":")
			self.lower = float( lower )
			self.upper = float( upper )

	def in_range( self, number ):
		if self.lower != None and number < self.lower:
			return False
		elif self.upper != None and number > self.upper:
			return False
		else:
			return True

	def is_below( self, number ):
		if self.lower !=None and number < self.lower:
			return True
		else:
			return False
	
	def is_above( self, number ):
		if self.upper !=None and number < self.upper:
			return True
		else:
			return False

	def get_distance( self, number ):
		if self.is_below( number ):
			return self.lower - number
		else:
			return number - self.upper

	def get_safety_margin( self, number, boundary ):
		if boundary == "lower":
			return number - self.lower
		else:
			return self.upper - number

	def __str__( self ):
		return str( self.lower ) + ":" + str( self.upper )

class field():
	"""A field object represents a field in a munin graph. It contains its
	name, current value plus warning and critical ranges. The warning and
	critical ranges may be an empty string, if no range is configured by
	munin. Current value and warn/crit ranges are coma-seperated, here are a
	few examples:
	* "Core 1=21.0,18:23,12:28"
	* "/dev/sda=34,32:38,"
	* "foo=12,,12:38
	"""

	def __init__( self, text ):
		self.fieldname, data = text.split( "=" )
		value, warn, crit = data.split( "," )
		self.value = float( value )
		
		if warn == '' or warn == ":":
			self.warn = None
		else:
			self.warn = range( warn )
			if self.warn.in_range( self.value):
				raise ValueError( "This is not a warning or critical value" )
		
		if crit == '' or crit == ":":
			self.crit = None
		else:
			self.crit = range( crit )
			if not self.warn and self.crit.in_range( self.value):
				raise ValueError( "This is not a warning or critical value" )

	def is_critical( self ):
		if not self.crit or self.crit.in_range( self.value ):
			return False
		
		return True

	def is_warning( self ):
		if not self.warn or self.warn.in_range( self.value ):
			return False

		if self.crit:
			if self.crit.in_range( self.value ):
				return True
			else:
				return False
		
		return True

	def __str__( self ):
		retVal = "* %s is at %s. This is " %(self.fieldname, self.value)
		
		if self.is_warning():
			if self.warn.is_below( self.value ):
				retVal += str(self.warn.get_distance(self.value)) \
					+ " below warning and " + str(self.crit.get_safety_margin(self.value, "lower" )) \
					+ " above critical."
			else:
				retVal += str(self.warn.get_distance(self.value)) \
					+ " above warning and " + str(self.crit.get_safety_margin(self.value, "upper" )) \
					+ " below critical."
		elif self.is_critical():
			if self.crit.is_below( self.value ):
				retVal += str(self.crit.get_distance(self.value)) + " below the critical threshold."
			else:
				retVal += str(self.crit.get_distance(self.value)) + " above the critical threshold."
		else:
			retVal +="Unknown"
		
		return retVal

# credentials for the bot
bot = { 'user':   config.get( 'xmpp', 'user' ),
	'server': config.get( 'xmpp', 'server' ),
	'resrc':  config.get( 'xmpp', 'resource' ),
	'passwd': config.get( 'xmpp', 'pass' )
}

# parse parameters
parser = OptionParser( version='1.0' )
group = OptionGroup( parser, "Required options" )
group.add_option( '--jid', dest='jid', type='string',
	help='The JID to send the warnings to.' )
group.add_option( '--host', dest='host', type='string',
	help='The host these warnings are for' )
group.add_option( '--graph', dest='graph', type='string',
	help='The graph that has a warning/critical condition. This is the '
	'same as the graph_title of the munin-plugin.' )
parser.add_option_group( group )

parser.add_option( '--critical', dest='critical', type='string',
	help='Fields with a "critical" value.' )
parser.add_option( '--warning', dest='warning', type='string',
	help='Fields with a "warning" value.' )
parser.add_option( '--unknown', dest='unknown', type='string',
	help='Fields with a "unknown" value.' )
parser.add_option( '--clean', dest='clean', action='store_true', default='False',
	help='Clean notifications older than 21600 secondes.' )
(options, args) = parser.parse_args()

# see if all required options (jid, host, graph) were given:
if (not options.jid or not options.host or not options.graph) and not options.clean:
	usage()

# connect to mysql database:
mysql_conn = MySQLdb.connect(
	host=config.get( 'mysql', 'host' ),
	user=config.get( 'mysql', 'user' ),
	passwd=config.get( 'mysql', 'pass' ),
	db=config.get( 'mysql', 'db' )
	)
mysql_cursor = mysql_conn.cursor()

if options.clean == True:
	stamp = get_stamp( 21600 )
	mysql_cursor.execute( "DELETE FROM alerts WHERE stamp < %s", (stamp) )
	mysql_cursor.close()
	mysql_conn.commit()
	mysql_conn.close()
	sys.exit()

# build subject and text:
subj = "Munin notification for %s" %(options.host)
text = "One or more fields on graph %s on %s are in warning or critical range.\n" %(options.graph, options.host)

def handle_fields( raw_fields, cond ):
	raw_fields = raw_fields.split( ";" )
	fields = []
	stamp = get_stamp( 21600 )

	for raw_field in raw_fields:
		print raw_field
		f = field( raw_field )
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

if options.critical:
	options.critical = handle_fields( options.critical, "critical" )
if options.warning:
	options.warning = handle_fields( options.warning, "warning" )
if options.unknown:
	options.unknown = handle_fields( options.unknown, "unknown" )

# sometimes we do get called with nothing to report:
if not options.critical and not options.warning and not options.unknown:
	log( "Called with nothing to report." )
	sys.exit(0)

if options.critical and len(options.critical) > 0:
	text += add_fields( "Critical", options.critical )
if options.warning and len(options.warning) > 0:
	text += add_fields( "Warning", options.warning )
if options.unknown and len(options.unknown) > 0:
	text += add_fields( "Unknown", options.unknown )

mysql_cursor.close()
mysql_conn.commit()
mysql_conn.close()

# Actually send the message via jabber:
cl = xmpp.Client( bot['server'], debug = [] )
cl.connect()
if cl.connected == '':
	raise RuntimeError( 'Could not connect to jabber server', bot['server'] )

x = cl.auth( bot['user'], bot['passwd'], bot['resrc'] )
if x == None:
	raise RuntimeError( 'Could not authenticate %s@%s' %(bot['user'], bot['passwd']) )
print 'here'
m = xmpp.protocol.Message( options.jid, text, subject=subj )
print m
id = cl.send( xmpp.protocol.Message( options.jid, text, subject=subj ) )
cl.disconnect()
