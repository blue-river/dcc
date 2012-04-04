from compiler import Asm, nextlabel
from codeitembase import CodeItemBase

class BooleanExpressionBase(CodeItemBase):

	constantExpression = False

class BooleanConstant(BooleanExpressionBase):

	argumentNames = ('value',)
	passiveArguments = ('value',)

	constantExpression = True

	def transformToAsm(self, containingFunction, containingLoop):
		yield Asm('comment', 'BooleanConstant')

		if self.value:
			yield Asm('SETB bit', 'ACC', 0)
		else:
			yield Asm('CLR bit', 'ACC', 0)

		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return 1

class GetBit(BooleanExpressionBase):

	argumentNames = ('expression', 'bit')
	passiveArguments = ('bit',)

	def resolveIdentifiers(self, containingModule):
		BooleanExpressionBase.resolveIdentifiers(self, containingModule)

		if self.bit > 7 or self.bit < 0:
			self.error("Bit '%d' out of range" % self.bit)

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.expression.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('comment', 'getbit')

		yield Asm('POP direct', 'ACC')
		yield Asm('MOV C,bit', 'ACC', self.bit)
		yield Asm('MOV bit,C', 'ACC', 0)
		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return self.expression.stackUsage(functions)

class Equals(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('POP direct', 'ACC')
		yield Asm('POP direct', 0)

		yield Asm('comment', '==')

		notequallabel = nextlabel('eq_notequal')
		endlabel = nextlabel('eq_end')

		yield Asm('CJNE A,direct,rel', 0, notequallabel)

		yield Asm('SETB bit', 'ACC', 0)
		yield Asm('SJMP rel', endlabel)

		yield Asm('label', notequallabel)
		yield Asm('CLR bit', 'ACC', 0)

		yield Asm('label', endlabel)
		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class NotEquals(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('POP direct', 'ACC')
		yield Asm('POP direct', 0)

		yield Asm('comment', '!=')

		notequallabel = nextlabel('neq_notequal')
		endlabel = nextlabel('neq_end')

		yield Asm('CJNE A,direct,rel', 0, notequallabel)

		yield Asm('CLR bit', 'ACC', 0)
		yield Asm('SJMP rel', endlabel)

		yield Asm('label', notequallabel)
		yield Asm('SETB bit', 'ACC', 0)

		yield Asm('label', endlabel)
		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class GreaterEquals(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('comment', '>=')

		carrylabel = nextlabel('geq_carry')
		endlabel = nextlabel('geq_end')

		yield Asm('POP direct', 0) # left
		yield Asm('POP direct', 'ACC') # right

		yield Asm('CLR C')
		yield Asm('SUBB A,Rn', 0) # left - right

		yield Asm('JC rel', carrylabel)

		yield Asm('SETB bit', 'ACC', 0)
		yield Asm('SJMP rel', endlabel)

		yield Asm('label', carrylabel)
		yield Asm('CLR bit', 'ACC', 0)

		yield Asm('label', endlabel)
		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class GreaterThan(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('comment', '>')

		carrylabel = nextlabel('gt_carry')
		endlabel = nextlabel('gt_end')

		yield Asm('POP direct', 'ACC') # right
		yield Asm('POP direct', 0) # left

		yield Asm('CLR C')
		yield Asm('SUBB A,Rn', 0) # right - left

		yield Asm('JC rel', carrylabel)

		yield Asm('CLR bit', 'ACC', 0)
		yield Asm('SJMP rel', endlabel)

		yield Asm('label', carrylabel)
		yield Asm('SETB bit', 'ACC', 0)

		yield Asm('label', endlabel)
		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class LessEquals(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('comment', '<=')

		carrylabel = nextlabel('leq_carry')
		endlabel = nextlabel('leq_end')

		yield Asm('POP direct', 'ACC') # right
		yield Asm('POP direct', 0) # left

		yield Asm('CLR C')
		yield Asm('SUBB A,Rn', 0) # right - left

		yield Asm('JC rel', carrylabel)

		yield Asm('SETB bit', 'ACC', 0)
		yield Asm('SJMP rel', endlabel)

		yield Asm('label', carrylabel)
		yield Asm('CLR bit', 'ACC', 0)

		yield Asm('label', endlabel)
		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class LessThan(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('comment', '<')

		carrylabel = nextlabel('lt_carry')
		endlabel = nextlabel('lt_end')

		yield Asm('POP direct', 0) # left
		yield Asm('POP direct', 'ACC') # right

		yield Asm('CLR C')
		yield Asm('SUBB A,Rn', 0) # left - right

		yield Asm('JC rel', carrylabel)

		yield Asm('CLR bit', 'ACC', 0)
		yield Asm('SJMP rel', endlabel)

		yield Asm('label', carrylabel)
		yield Asm('SETB bit', 'ACC', 0)

		yield Asm('label', endlabel)
		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)
