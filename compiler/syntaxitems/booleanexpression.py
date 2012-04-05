from compiler import *
from codeitembase import CodeItemBase

class BooleanExpressionBase(CodeItemBase):

	constantExpression = False

class BooleanConstant(BooleanExpressionBase):

	argumentNames = ('value',)
	passiveArguments = ('value',)

	constantExpression = True

	def transformToAsm(self, containingFunction, containingLoop):
		yield Instruction(Comment, 'BooleanConstant')

		if self.value:
			yield Instruction(SET, Push(), Literal(1))
		else:
			yield Instruction(SET, Push(), Literal(0))

	def stackUsage(self, functions):
		return 1

class GetBit(BooleanExpressionBase):

	argumentNames = ('expression', 'bit')
	passiveArguments = ('bit',)

	def resolveIdentifiers(self, containingModule):
		BooleanExpressionBase.resolveIdentifiers(self, containingModule)

		if self.bit > 15 or self.bit < 0:
			self.error("Bit '%d' out of range" % self.bit)

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.expression.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, 'getbit')
		# TODO?

		bitSetLabel = nextlabel('getbit_set')
		endLabel = nextlabel('getbit_end')

		yield Instruction(IFB, Pop(), Literal(1 << self.bit))
		yield Instruction(SET, PC(), bitSetLabel)
		yield Instruction(SET, Push(), Literal(0))
		yield Instruction(SET, PC(), endLabel)
		yield Instruction(Label, bitSetLabel)
		yield Instruction(SET, Push(), Literal(1))
		yield Instruction(Label, endLabel)

	def stackUsage(self, functions):
		return self.expression.stackUsage(functions)

class Equals(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '==')

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

class NotEquals(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '!=')

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

class GreaterEquals(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '>=')

		greaterEqualsLabel = nextlabel('geq_true')
		endLabel = nextlabel('end')

		yield Instruction(SET, TempStorage, Pop()) # right
		yield Instruction(IFG, TempStorage, Pop())
		yield Instruction(SET, PC(), greaterEqualsLabel)
		yield Instruction(SET, Push(), Literal(0))
		yield Instruction(SET, PC(), endLabel)
		yield Instruction(Label, greaterEqualsLabel)
		yield Instruction(SET, Push(), Literal(1))
		yield Instruction(Label, endLabel)

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class GreaterThan(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '>')

		greaterLabel = nextlabel('gt_true')
		endlabel = nextlabel('gt_end')

		yield Instruction(SET, TempStorage, Pop()) # right
		yield Instruction(IFG, Pop(), TempStorage)
		yield Instruction(SET, PC(), greaterLabel)
		yield Instruction(SET, Push(), Literal(0))
		yield Instruction(SET, PC(), endlabel)
		yield Instruction(Label, greaterLabel)
		yield Instruction(SET, Push(), Literal(1))
		yield Instruction(Label, endlabel)

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class LessEquals(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '<=')

		greaterLabel = nextlabel('gt_true')
		endlabel = nextlabel('gt_end')

		yield Instruction(SET, TempStorage, Pop()) # right
		yield Instruction(IFG, Pop(), TempStorage)
		yield Instruction(SET, PC(), greaterLabel)
		yield Instruction(SET, Push(), Literal(1))
		yield Instruction(SET, PC(), endlabel)
		yield Instruction(Label, greaterLabel)
		yield Instruction(SET, Push(), Literal(0))
		yield Instruction(Label, endlabel)

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class LessThan(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, '<')

		greaterEqualsLabel = nextlabel('geq_true')
		endLabel = nextlabel('end')

		yield Instruction(SET, TempStorage, Pop()) # right
		yield Instruction(IFG, TempStorage, Pop())
		yield Instruction(SET, PC(), greaterEqualsLabel)
		yield Instruction(SET, Push(), Literal(1))
		yield Instruction(SET, PC(), endLabel)
		yield Instruction(Label, greaterEqualsLabel)
		yield Instruction(SET, Push(), Literal(0))
		yield Instruction(Label, endLabel)

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)
