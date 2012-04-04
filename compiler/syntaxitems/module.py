from abstractsyntaxitem import AbstractSyntaxItem

class Module(AbstractSyntaxItem):

	def __init__(self, filename, line, name, datafields, functions):
		AbstractSyntaxItem.__init__(self, filename, line)

		self.name = name

		self.datafields = datafields
		self.functions = functions

	def resolveIdentifiers(self):
		for datafield in self.datafields:
			datafield.resolveIdentifiers(self)

		for function in self.functions:
			function.resolveIdentifiers(self)
