from abstractsyntaxitem import AbstractSyntaxItem

class DataField(AbstractSyntaxItem):

	constant = False

	default = None

	predefined = False
	assigned = False
	read = False

	def __init__(self, filename, line, datatype, name):
		AbstractSyntaxItem.__init__(self, filename, line)

		if datatype == 'void':
			self.error("Illegal data type: 'void' is not a valid data type for fields")

		self.name = name
		self.datatype = datatype

	def resolveIdentifiers(self, containingModule):
		self.name = containingModule.name + '.' + self.name
		self.containingModule = containingModule.name

class ConstantDataField(DataField):

	constant = True

	assigned = True

	def __init__(self, filename, line, datatype, name, value):
		DataField.__init__(self, filename, line, datatype, name)

		self.value = value

	address = None

class LocalVariable(DataField):

	address = None
