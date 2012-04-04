from compiler import Asm
from booleanexpression import BooleanExpressionBase

class BooleanAnd(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('comment', '&&')

		yield Asm('POP direct', 'ACC')
		yield Asm('POP direct', 0)

		yield Asm('ANL A,Rn', 0)
		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class BooleanEquals(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('comment', 'boolean ==')

		yield Asm('POP direct', 'ACC')
		yield Asm('POP direct', 0)
		yield Asm('XRL A,Rn', 0)
		yield Asm('CPL A')
		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class BooleanNotEquals(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('comment', 'boolean !=')

		yield Asm('POP direct', 'ACC')
		yield Asm('POP direct', 0)
		yield Asm('XRL A,Rn', 0)
		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)

class BooleanNot(BooleanExpressionBase):

	argumentNames = ('value',)

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.value.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('comment', '!')

		yield Asm('POP direct', 'ACC')
		yield Asm('CPL bit', 'ACC', 0)
		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return self.value.stackUsage(functions)

class BooleanOr(BooleanExpressionBase):

	argumentNames = ('left', 'right')

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.left.transformToAsm(containingFunction, containingLoop):
			yield instruction
		for instruction in self.right.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('comment', '||')
		
		yield Asm('POP direct', 'ACC')
		yield Asm('POP direct', 0)

		yield Asm('ANL A,Rn', 0)
		yield Asm('PUSH direct', 'ACC')

	def stackUsage(self, functions):
		return max(self.left.stackUsage(functions), self.right.stackUsage(functions) + 1)
