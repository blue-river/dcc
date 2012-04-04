from compiler import *
from codeitembase import CodeItemBase

class Break(CodeItemBase):

	argumentNames = ()

	def transformToAsm(self, containingFunction, containingLoop):
		if containingLoop is None:
			self.error('break outside loop')

		yield Instruction(Comment, 'break')

		yield Instruction(SET, PC(), containingLoop.endlabel)

	def stackUsage(self, functions):
		return 0

class Continue(CodeItemBase):

	argumentNames = ()

	def transformToAsm(self, containingFunction, containingLoop):
		if containingLoop is None:
			self.error('continue outside loop')

		yield Instruction(Comment, 'continue')

		yield Instruction(SET, PC(), containingLoop.startlabel)

	def stackUsage(self, functions):
		return 0

class If(CodeItemBase):

	argumentNames = ('predicate', 'then', 'else_')
	passiveArguments = ('operator',)

	def transformToAsm(self, containingFunction, containingLoop):
		for instruction in self.predicate.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(Comment, 'if')

		thenlabel = nextlabel('if_then')
		endlabel = nextlabel('if_end')

		yield Instruction(IFE, Pop(), Literal(0))
		yield Instruction(SET, SP(), thenlabel)

		for instruction in self.else_.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(SET, SP(), endlabel)
		yield Instruction(Label, thenlabel)

		for instruction in self.then.transformToAsm(containingFunction, containingLoop):
			yield instruction
		
		yield Instruction(Label, endlabel)

	def stackUsage(self, functions):
		return max(self.predicate.stackUsage(functions), self.then.stackUsage(functions), self.else_.stackUsage(functions))

class Loop(CodeItemBase):

	argumentNames = ('body',)

	def transformToAsm(self, containingFunction, containingLoop):
		self.startlabel = nextlabel('loop_start')
		self.endlabel = nextlabel('loop_end')

		yield Instruction(Comment, 'loop')

		yield Instruction(Label, self.startlabel)

		for instruction in self.body.transformToAsm(containingFunction, self):
			yield instruction

		yield Instruction(SET, SP(), self.startlabel)
		yield Instruction(Label, self.endlabel)

	def stackUsage(self, functions):
		return self.body.stackUsage(functions)

class Repeat(CodeItemBase):

	argumentNames = ('repeatcount', 'body')

	def transformToAsm(self, containingFunction, containingLoop):
		self.startlabel = nextlabel('repeat_start')
		self.endlabel = nextlabel('repeat_end')
		self.djnzrepeatlabel = nextlabel('repeat_djnzrepeat')

		yield Asm('comment', 'repeat')

		# save the current repeat counter
		yield Asm('PUSH direct', 1)

		# get the new repeat counter
		for instruction in self.repeatcount.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Asm('POP direct', 1)

		# don't execute if the counter is 0
		yield Asm('CJNE Rn,#data,rel', 1, 0, self.startlabel)
		yield Asm('LJMP addr16', self.endlabel)

		# loop
		yield Asm('label', self.startlabel)

		for instruction in self.body.transformToAsm(containingFunction, self):
			yield instruction

		yield Asm('DJNZ Rn,rel', 1, self.djnzrepeatlabel)
		yield Asm('SJMP rel', self.endlabel)

		yield Asm('label', self.djnzrepeatlabel)
		yield Asm('LJMP addr16', self.startlabel)

		yield Asm('label', self.endlabel)

		# restore the old repeat counter
		yield Asm('POP direct', 1)

	def stackUsage(self, functions):
		return max(self.repeatcount.stackUsage(functions), self.body.stackUsage(functions) + 1)

class While(CodeItemBase):

	argumentNames = ('condition', 'body')

	def transformToAsm(self, containingFunction, containingLoop):
		self.startlabel = nextlabel('while_start')
		self.endlabel = nextlabel('while_end')
		self.jnbcontinuelabel = nextlabel('while_jnbcontinue')
		self.jnbendlabel = nextlabel('while_jnbendlabel')

		yield Asm('comment', 'while')

		yield Asm('label', self.startlabel)

		for instruction in self.condition.transformToAsm(containingFunction, self):
			yield instruction

		yield Asm('POP direct', 'ACC')

		yield Asm('JNB bit,rel', 'ACC', 0, self.jnbendlabel)
		yield Asm('SJMP rel', self.jnbcontinuelabel)

		yield Asm('label', self.jnbendlabel)
		yield Asm('LJMP addr16', self.endlabel)

		yield Asm('label', self.jnbcontinuelabel)

		for instruction in self.body.transformToAsm(containingFunction, self):
			yield instruction

		yield Asm('LJMP addr16', self.startlabel)
		yield Asm('label', self.endlabel)

	def stackUsage(self, functions):
		return max(self.condition.stackUsage(functions), self.body.stackUsage(functions))
