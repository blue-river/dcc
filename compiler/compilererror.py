class CompilerError(Exception):
	"""Error class for errors in the compiler input."""

	def __init__(self, filename, line, msg):
		self.filename = filename
		self.line = line
		self.msg = msg

	def __str__(self):
		if self.filename is None:
			return self.msg
		
		if self.line is None:
			return "%s: %s" % (self.filename, self.msg)

		return "%s:%s: %s" % (self.filename, self.line, self.msg)
