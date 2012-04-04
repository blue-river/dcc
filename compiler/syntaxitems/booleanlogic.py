from compiler import *
from booleanexpression import BooleanExpressionBase

class BooleanAnd(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, 'boolean &&')

		yield Instruction(SET, A, Pop())
		yield Instruction(AND, Peek(), A)

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class BooleanEquals(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, 'boolean ==')

		notequallabel = nextlabel('eq_notequal')
		endlabel = nextlabel('eq_end')

		yield Instruction(IFN, Pop(), Pop())
		yield Instruction(SET, PC(), notequallabel)
		yield Instruction(SET, Push(), Literal(1))
		yield Instruction(SET, PC(), endlabel)
		yield Instruction(Label, notequallabel)
		yield Instruction(SET, Push(), Literal(0))
		yield Instruction(Label, endlabel)

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class BooleanNotEquals(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, 'boolean !=')

		equallabel = nextlabel('neq_equal')
		endlabel = nextlabel('neq_end')

		yield Instruction(IFE, Pop(), Pop())
		yield Instruction(SET, PC(), equallabel)
		yield Instruction(SET, Push(), Literal(1))
		yield Instruction(SET, PC(), endlabel)
		yield Instruction(Label, equallabel)
		yield Instruction(SET, Push(), Literal(0))
		yield Instruction(Label, endlabel)

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class BooleanNot(BooleanExpressionBase):

	argumentNames = ('value',)

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.value.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, 'boolean !')

		yield Instruction(XOR, Peek(), 1)

	def stackUsage(self, functions):
		return self.value.stackUsage(functions)

class BooleanOr(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, 'boolean |')

		yield Instruction(SET, A, Pop())
		yield Instruction(BOR, Peek(), A)

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)
