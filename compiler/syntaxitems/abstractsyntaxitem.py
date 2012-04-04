from compiler import CompilerError

class AbstractSyntaxItem(object):

	def __init__(self, filename, line):
		self.filename = filename
		self.line = line

	def error(self, message):
		raise CompilerError(self.filename, self.line, message)
