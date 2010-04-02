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
