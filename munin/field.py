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
		self.fieldname, data = text.split( "=" )
		value, warn, crit = data.split( "," )
		self.value = float( value )

		if warn == '' or warn == ":":
			self.warn = None
		else:   
			self.warn = range.range( warn )
			if self.warn.in_range( self.value):
				raise ValueError( "This is not a warning or critical value" )

		if crit == '' or crit == ":":
			self.crit = None
		else:   
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
