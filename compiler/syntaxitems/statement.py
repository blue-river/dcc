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

		yield Instruction(Comment, 'setbit not yet supported')
		# TODO
		return

		if not self.value.constantExpression:
			yield Asm('POP direct', 'ACC')
			yield Asm('MOV C,bit', 'ACC', 0)

		if '.' in self.target:
			# identifier is a data field
			location = containingFunction.identifiers[self.target].location

			if location == 'internal':
				yield Asm('MOV direct,direct', 'ACC', self.target)
			elif location == 'external':
				yield Asm('MOV DPTR,#data16', self.target)
				yield Asm('MOVX A,@DPTR')
			else:
				raise Exception("Internal error: unknown data type location '%s'" % location)

			if self.value.constantExpression:
				if self.value.value:
					yield Asm('SETB bit', 'ACC', self.bit)
				else:
					yield Asm('CLR bit', 'ACC', self.bit)
			else:
				yield Asm('MOV bit,C', 'ACC', self.bit)

			if location == 'internal':
				yield Asm('MOV direct,direct', self.target, 'ACC')
			elif location == 'external':
				yield Asm('MOVX @DPTR,A')
			else:
				raise Exception("Internal error: unknown data type location '%s'" % location) 
		else:
			# identifier is a local variable
			yield Asm('MOV direct,Rn', 'ACC', containingFunction.getRegisterForVariable(self.target))

			if self.value.constantExpression:
				if self.value.value:
					yield Asm('SETB bit', 'ACC', self.bit)
				else:
					yield Asm('CLR bit', 'ACC', self.bit)
			else:
				yield Asm('MOV bit,C', 'ACC', self.bit)

			yield Asm('MOV Rn,direct', containingFunction.getRegisterForVariable(self.target), 'ACC')


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
			location = containingFunction.identifiers[self.target].location

			yield Instruction(SET, Pointer(self.target), Pop())
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

			if location == 'internal':
				yield Asm('DEC direct', self.target)
			elif location == 'external':
				yield Asm('MOV DPTR,#data16', self.target)
				yield Asm('MOVX A,@DPTR')
				yield Asm('DEC ACC')
				yield Asm('MOVX @DPTR,A')
			else:
				raise Exception("Internal error: unknown data type location '%s'" % location) 
		else:
			# identifier is a local variable
			yield Asm('DEC direct', containingFunction.getRegisterForVariable(self.target))

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

			if location == 'internal':
				yield Asm('INC direct', self.target)
			elif location == 'external':
				yield Asm('MOV DPTR,#data16', self.target)
				yield Asm('MOVX A,@DPTR')
				yield Asm('INC ACC')
				yield Asm('MOVX @DPTR,A')
			else:
				raise Exception("Internal error: unknown data type location '%s'" % location) 
		else:
			# identifier is a local variable
			yield Asm('INC direct', containingFunction.getRegisterForVariable(self.target))

	def stackUsage(self, functions):
		return 0

class Return(CodeItemBase):

	argumentNames = ()

	def transformToAsm(self, containingFunction, containingLoop):
		if containingFunction.datatype != 'void':
			self.error("Functions with data type '%s' cannot return without a value" % containingFunction.datatype)

		yield Instruction(Comment, 'return')

		yield Instruction(SET, PC(), Literal('ret_' + containingFunction.name))

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
		yield Instruction(SET, PC(), Literal('ret_' + containingFunction.name))

	def stackUsage(self, functions):
		return self.value.stackUsage(functions)
