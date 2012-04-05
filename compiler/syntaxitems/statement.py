from compiler import *
from codeitembase import CodeItemBase

class SetBit(CodeItemBase):

	argumentNames = ('target', 'bit', 'value')
	passiveArguments = ('target', 'bit')

	def resolveIdentifiers(self, containingModule):
		CodeItemBase.resolveIdentifiers(self, containingModule)

		if self.bit > 7 or self.bit < 0:
			self.error("Bit '%d' out of range" % self.bit)

	def verifyIdentifiers(self, datafields, functions, containingFunction):
		CodeItemBase.verifyIdentifiers(self, datafields, functions, containingFunction)

		if self.target not in containingFunction.argdict and self.target not in containingFunction.localdict and self.target not in datafields:
			qualName = '%s.%s' % (self.containingModule, self.target)
			if qualName in datafields:
				self.target = qualName
			else:
				self.error("Data field '%s' not found" % self.target)

	def transformToAsm(self, containingFunction, containingLoop):
		if containingFunction.identifiers[self.target].constant:
			self.error("Constant field '%s' cannot be assigned to" % self.target)

		if not self.value.constantExpression:
			for instruction in self.value.transformToAsm(containingFunction, containingLoop):
				yield instruction

		yield Instruction(Comment, 'setbit')

		if '.' in self.target:
			# identifier is a data field
			target = DataField(containingFunction.identifiers[self.target])
		else:
			target = containingFunction.getRegisterForVariable(self.target)

		if self.value.constantExpression:
			if self.value.value:
				yield Instruction(BOR, target, Literal(1 << self.bit))
			else:
				yield Instruction(AND, target, Literal(0xffff ^ (1 << self.bit)))
		else:
			yield Instruction(IFE, Pop(), Literal(0))
			yield Instruction(SET, PC(), clearBitLabel)

			yield Instruction(BOR, target, Literal(1 << self.bit))
			yield Instruction(SET, PC(), endLabel)

			yield Instruction(Label, clearBitLabel)
			yield Instruction(AND, target, Literal(0xffff ^ (1 << self.bit)))

			yield Instruction(Label, endLabel)

	def stackUsage(self, functions):
		return self.value.stackUsage(functions)

class Assignment(CodeItemBase):

	argumentNames = ('target', 'value')
	passiveArguments = ('target',)

	def verifyIdentifiers(self, datafields, functions, containingFunction):
		CodeItemBase.verifyIdentifiers(self, datafields, functions, containingFunction)

		if self.target not in containingFunction.identifiers:
			qualName = '%s.%s' % (self.containingModule, self.target)
			if qualName in datafields:
				self.target = qualName
			else:
				self.error("Data field '%s' not found" % self.target)

		containingFunction.identifiers[self.target].assigned = True

	def transformToAsm(self, containingFunction, containingLoop):
		if containingFunction.identifiers[self.target].constant:
			self.error("Constant field '%s' cannot be assigned to" % self.target)

		for instruction in self.value.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, 'assignment')

		if '.' in self.target:
			# identifier is a data field
			dataField = containingFunction.identifiers[self.target]

			yield Instruction(SET, DataField(dataField), Pop())
		else:
			# identifier is a local variable
			yield Instruction(SET, containingFunction.getRegisterForVariable(self.target), Pop())

	def stackUsage(self, functions):
		return self.value.stackUsage(functions)

class Discard(CodeItemBase):

	argumentNames = ('expression',)

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.expression.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, 'discard')
		yield Instruction(ADD, SP(), Literal(1))

		# TODO: discard words specified by data type

	def stackUsage(self, functions):
		return self.expression.stackUsage(functions)

class Decrement(CodeItemBase):

	argumentNames = ('target',)
	passiveArguments = ('target',)

	def verifyIdentifiers(self, datafields, functions, containingFunction):
		CodeItemBase.verifyIdentifiers(self, datafields, functions, containingFunction)

		if self.target not in containingFunction.identifiers:
			qualName = '%s.%s' % (self.containingModule, self.target)
			if qualName in datafields:
				self.target = qualName
			else:
				self.error("Data field '%s' not found" % self.target)

		containingFunction.identifiers[self.target].assigned = True

	def transformToAsm(self, containingFunction, containingLoop):
		if '.' in self.target:
			# identifier is a data field
			location = containingFunction.identifiers[self.target].location

			yield Instruction(SUB, Pointer(self.target), 1)
		else:
			# identifier is a local variable
			yield Instruction(SUB, containingFunction.getRegisterForVariable(self.target), 1)

	def stackUsage(self, functions):
		return 0

class Increment(CodeItemBase):

	argumentNames = ('target',)
	passiveArguments = ('target',)

	def verifyIdentifiers(self, datafields, functions, containingFunction):
		CodeItemBase.verifyIdentifiers(self, datafields, functions, containingFunction)

		if self.target not in containingFunction.identifiers:
			qualName = '%s.%s' % (self.containingModule, self.target)
			if qualName in datafields:
				self.target = qualName
			else:
				self.error("Data field '%s' not found" % self.target)

		containingFunction.identifiers[self.target].assigned = True

	def transformToAsm(self, containingFunction, containingLoop):
		if '.' in self.target:
			# identifier is a data field
			location = containingFunction.identifiers[self.target].location

			yield Instruction(ADD, Pointer(self.target), 1)
		else:
			# identifier is a local variable
			yield Instruction(ADD, containingFunction.getRegisterForVariable(self.target), 1)

	def stackUsage(self, functions):
		return 0

class Return(CodeItemBase):

	argumentNames = ()

	def transformToAsm(self, containingFunction, containingLoop):
		if containingFunction.datatype != 'void':
			self.error("Functions with data type '%s' cannot return without a value" % containingFunction.datatype)

		yield Instruction(Comment, 'return')

		yield Instruction(SET, PC(), LabelReference('ret_' + containingFunction.name))

	def stackUsage(self, functions):
		return 0

class ReturnValue(CodeItemBase):

	argumentNames = ('value',)

	def transformToAsm(self, containingFunction, containingLoop):
		if containingFunction.datatype == 'void':
			self.error("A value cannot be returned from 'void' functions")

		for instruction in self.value.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, 'return')
		yield Instruction(SET, O(), Pop())
		yield Instruction(SET, PC(), LabelReference('ret_' + containingFunction.name))

	def stackUsage(self, functions):
		return self.value.stackUsage(functions)
