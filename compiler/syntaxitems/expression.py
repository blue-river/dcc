from compiler import *
from codeitembase import CodeItemBase

class ExpressionBase(CodeItemBase):

	constantExpression = False

class Addition(ExpressionBase):
	
	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '+')

		yield Instruction(SET, A, Pop())
		yield Instruction(ADD, Peek(), A)

	def stackUsage(self, functions):
		return max(self.right.stackUsage(functions), self.left.stackUsage(functions) + 1)

class And(ExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '&')

		yield Instruction(SET, A, Pop())
		yield Instruction(AND, Peek(), A)

	def stackUsage(self, functions):
		return max(self.right.stackUsage(functions), self.left.stackUsage(functions) + 1)

class Call(ExpressionBase):

	argumentNames = ('function', 'arglist')
	passiveArguments = ('function', 'arglist')

	def resolveIdentifiers(self, containingModule):
		ExpressionBase.resolveIdentifiers(self, containingModule)

		if '.' not in self.function:
			self.function = containingModule.name + '.' + self.function

		for arg in self.arglist:
			arg.resolveIdentifiers(containingModule)
	
	def verifyIdentifiers(self, datafields, functions, containingFunction):
		ExpressionBase.verifyIdentifiers(self, datafields, functions, containingFunction)

		if self.function not in functions:
			self.error("Function '%s' not found" % self.function)

		for function in functions.values():
			if function.name != self.function:
				continue
			if len(function.args) != len(self.arglist):
				self.error("Function '%s' called with %d arguments (expected %d)" % (self.function, len(self.arglist), len(function.args)))

			function.called = True

		for arg in self.arglist:
			arg.verifyIdentifiers(datafields, functions, containingFunction)
			
	def transformToAsm(self, containingFunction, containingLoop):
		for arg in self.arglist:
			for asm in arg.transformToAsm(containingFunction, containingLoop):
				yield asm

		yield Instruction(Comment, 'call')

		# TODO
		address = 0x07 + len(self.arglist)

		for arg in self.arglist:
			yield Asm('POP direct', address)
			address -= 1

		yield Instruction(JSR, 'func_' + self.function)
		# TODO: don't push for void functions.
		yield Instruction(SET, Push(), A)

	def stackUsage(self, functions):
		maxStack = 0

		for i in xrange(len(self.arglist)):
			maxStack = max(maxStack, self.arglist[i].stackUsage(functions) + i)

		return max(maxStack, functions[self.function].stackUsage(functions) + 2)

class Constant(ExpressionBase):

	argumentNames = ('value',)
	passiveArguments = ('value',)

	constantExpression = True

	def transformToAsm(self, containingFunction, containingLoop):
		yield Instruction(Comment, 'constant')

		yield Instruction(SET, Push(), Literal(self.value))

	def stackUsage(self, functions):
		return 1

class Identifier(ExpressionBase):

	argumentNames = ('name',)
	passiveArguments = ('name',)

	def verifyIdentifiers(self, datafields, functions, containingFunction):
		ExpressionBase.verifyIdentifiers(self, datafields, functions, containingFunction)

		if self.name not in containingFunction.identifiers:
			qualName = '%s.%s' % (self.containingModule, self.name)
			if qualName in datafields:
				self.name = qualName
			else:
				self.error("Data field '%s' not found" % self.name)

		containingFunction.identifiers[self.name].read = True

	def transformToAsm(self, containingFunction, containingLoop):
		yield Instruction(Comment, 'identifier')

		if containingFunction.identifiers[self.name].constant:
			# identifier is a constant data field
			yield Instruction(SET, Push(), Literal(containingFunction.identifiers[self.name].value))
		elif '.' in self.name:
			# identifier is a data field

			location = containingFunction.identifiers[self.name].location

			yield Instruction(SET, Push(), self.name)
		else:
			# identifier is a local variable
			yield Instruction(SET, Push(), containingFunction.getRegisterForVariable(self.name))

	def stackUsage(self, functions):
		return 1

class Multiplication(ExpressionBase):
	
	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '*')

		yield Instruction(SET, A, Pop())
		yield Instruction(MUL, Peek(), A)

	def stackUsage(self, functions):
		return max(self.right.stackUsage(functions), self.left.stackUsage(functions) + 1)

class Not(ExpressionBase):

	argumentNames = ('expression',)

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.expression.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '!')

		yield Instruction(XOR, Peek(), Literal(0xffff))

	def stackUsage(self, functions):
		return self.expression.stackUsage(functions)

class Or(ExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '|')

		yield Instruction(SET, A, Pop())
		yield Instruction(BOR, Peek(), A)

	def stackUsage(self, functions):
		return max(self.right.stackUsage(functions), self.left.stackUsage(functions) + 1)

class Subtraction(ExpressionBase):
	
	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '-')

		yield Instruction(SET, A, Pop())
		yield Instruction(SUB, Peek(), A)

	def stackUsage(self, functions):
		return max(self.right.stackUsage(functions), self.left.stackUsage(functions) + 1)

class Xor(ExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '^')

		yield Instruction(SET, A, Pop())
		yield Instruction(XOR, Peek(), A)

	def stackUsage(self, functions):
		return max(self.right.stackUsage(functions), self.left.stackUsage(functions) + 1)
