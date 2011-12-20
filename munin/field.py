import range

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
		self.warn = None
		self.crit = None
		self.value = None

		self.fieldname, data = text.split( "=" )
		value, warn, crit = data.split( "," )
		if value != "unknown":
			self.value = float( value )

		if warn != '' and warn != ":" and value:
			self.warn = range.range( warn )
			if self.warn.in_range( self.value):
				raise ValueError( "This is not a warning or critical value" )

		if crit != '' and crit != ":" and value:
			self.crit = range.range( crit )
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
		retVal = "* %s is at %s (" %(self.fieldname, self.value)

		if self.is_warning():
			if self.warn.is_below( self.value ):
				retVal += '%s below warning, %s above critical)' % \
					(self.warn.get_distance(self.value),
					 self.crit.get_safety_margin(self.value, "lower" ))
			else:
				retVal += '%s above warning, %s below critical)' % \
					(self.warn.get_distance(self.value),
					 self.crit.get_safety_margin(self.value, "upper" ))
		elif self.is_critical():
			if self.crit.is_below( self.value ):
				retVal += "%s below critical)" % self.crit.get_distance(self.value)
			else:
				retVal += "%s above critical)" % self.crit.get_distance(self.value)
		else:
			retVal +="Unknown"

		return retVal
