#!/usr/bin/python

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

import sys, xmpp, time, ConfigParser

# set to True for debugging:
debug = True
log_file = '/var/log/munojabo.log'

# config-file
config = ConfigParser.ConfigParser()
config.read( '/etc/munojabo.conf' )

# credentials for the bot
bot = { 'user':   config.get( 'munojabo', 'user' ),
	'server': config.get( 'munojabo', 'server' ),
	'resrc':  config.get( 'munojabo', 'resource' ),
	'passwd': config.get( 'munojabo', 'password' )
}


def log( message ):
	print message
	if debug:
		stamp = str(time.strftime( '%Y-%m-%d %H:%M:%S' ))
		fi = open( log_file, 'a' )
		fi.write( stamp + ": " + message + "\n" )
		fi.close()

def usage( exitcode = 1 ):
	print "Please see the README-file for documentation on how to use this script."
	sys.exit( exitcode )

class range():
	"""A range object is a warning/critical range as configured by munin. It
	might have an upper and a lower bound or only one of each. Here are
	three examples of valid ranges: 10:20, 10:, :20.
	
	Note that a range may be non-existent (e.g. if no warning range is
	given.)"""

	def __init__( self, text ):
		print "range: " + text
		self.lower = None
		self.upper = None

		if text == "":
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
		self.warn = range( warn )
		self.crit = range( crit )

	def __str__( self ):
		retVal = "* " + self.fieldname + " is at " + str( self.value) + ". This is "

		if self.crit.in_range( self.value ): # this is only a warning
			if self.warn.is_below( self.value ):
				retVal += str(self.warn.get_distance(self.value)) \
					+ " below warning and " + str(self.crit.get_safety_margin(self.value, "lower" )) \
					+ " above critical."
			else:
				retVal += str(self.warn.get_distance(self.value)) \
					+ " above warning and " + str(self.crit.get_safety_margin(self.value, "upper" )) \
					+ " below critical."
		else: # this is critical:
			if self.crit.is_below( self.value ):
				retVal += str(self.crit.get_distance(self.value)) + " below the critical threshold."
			else:
				retVal += str(self.crit.get_distance(self.value)) + " above the critical threshold."
				
		return retVal + "\n"



# parse parameters
log( str( sys.argv[1:] ) )
if len( sys.argv ) != 7:
	log( "Bad number (" + str(len(sys.argv)) + " instead of 7) of command line arguments." )
	usage()

jid=sys.argv[1]
host=sys.argv[2]
graph=sys.argv[3]
warn=sys.argv[4]
crit=sys.argv[5]
unkn=sys.argv[6]

if not warn.startswith( "--warnings=" ):
	log( "4th argument doesn't start with \"--warnings=\"" )
	usage()
else:
	warn = warn[11:]
if not crit.startswith( "--critical=" ):
	log( "5th argument doesn't start with \"--critical=\"" )
	usage()
else:
	crit = crit[11:]
if not unkn.startswith( "--unknown=" ):
	log( "6th argument doesn't start with \"--unknown=\"" )
	usage()
else:
	unkn = unkn[10:]

# build subject and text:
subj = "Munin notification for " + host
text = "One or more fields on graph \"" + graph + "\" on " + host + " are in warning or critical range."

if crit == "" and warn == "" and unkn == "":
	log( "Called with nothing to report." )
	sys.exit(0)

# critical is first:
if crit != "":
	text += "\nCritical:\n"
	for raw_field in crit.split( ";" ):
		text += str( field( raw_field ) )

# also attach warning messages:
if warn != "":
	text += "\nWarnings:\n"
	for raw_field in warn.split( ";" ):
		text += str( field( raw_field ) )

if unkn != "":
	text += "\nUnknown:\n"
	for raw_field in unkn.split( ";" ):
		text += str( field( raw_field ) )

"""Actually send the message via jabber:"""
cl = xmpp.Client( bot['server'], debug = [] )
cl.connect()
cl.auth( bot['user'], bot['passwd'], bot['resrc'] )
id = cl.send( xmpp.protocol.Message( jid, text, subject=subj ) )
cl.disconnect()
