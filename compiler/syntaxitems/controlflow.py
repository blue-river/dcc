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

		elselabel = nextlabel('if_else')
		endlabel = nextlabel('if_end')

		yield Instruction(IFE, Pop(), Literal(1))
		yield Instruction(SET, PC(), elselabel)

		for instruction in self.then.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(SET, PC(), endlabel)
		yield Instruction(Label, elselabel)

		for instruction in self.else_.transformToAsm(containingFunction, containingLoop):
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

		yield Instruction(SET, PC(), self.startlabel)
		yield Instruction(Label, self.endlabel)

	def stackUsage(self, functions):
		return self.body.stackUsage(functions)

class Repeat(CodeItemBase):

	argumentNames = ('repeatcount', 'body')

	def transformToAsm(self, containingFunction, containingLoop):
		self.startlabel = nextlabel('repeat_start')
		self.endlabel = nextlabel('repeat_end')
		self.djnzrepeatlabel = nextlabel('repeat_djnzrepeat')

		yield Instruction(Comment, 'repeat')

		# save the current repeat counter
		yield Instruction(SET, Push(), RepeatCounter)

		# get the new repeat counter
		for instruction in self.repeatcount.transformToAsm(containingFunction, containingLoop):
			yield instruction

		yield Instruction(SET, RepeatCounter, Pop())

		# loop
		yield Instruction(Label, self.startlabel)

		# exit loop if the counter is 0
		yield Instruction(IFE, RepeatCounter, Literal(0))
		yield Instruction(SET, PC(), self.endlabel)

		for instruction in self.body.transformToAsm(containingFunction, self):
			yield instruction

		yield Instruction(SUB, RepeatCounter, Literal(1))
		yield Instruction(SET, PC(), self.startlabel)

		yield Instruction(Label, self.endlabel)
		yield Instruction(SET, RepeatCounter, Pop())

	def stackUsage(self, functions):
		return max(self.repeatcount.stackUsage(functions), self.body.stackUsage(functions)) + 1

class While(CodeItemBase):

	argumentNames = ('condition', 'body')

	def transformToAsm(self, containingFunction, containingLoop):
		self.startlabel = nextlabel('while_start')
		self.endlabel = nextlabel('while_end')

		yield Instruction(Comment, 'while')

		yield Instruction(Label, self.startlabel)

		for instruction in self.condition.transformToAsm(containingFunction, self):
			yield instruction

		yield Instruction(IFE, Pop(), Literal(0))
		yield Instruction(SET, PC(), self.endlabel)

		for instruction in self.body.transformToAsm(containingFunction, self):
			yield instruction

		yield Instruction(SET, PC(), self.startlabel)
		yield Instruction(Label, self.endlabel)

	def stackUsage(self, functions):
		return max(self.condition.stackUsage(functions), self.body.stackUsage(functions))
