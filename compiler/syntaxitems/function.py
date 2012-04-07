from compiler import *
from codeitembase import CodeItemBase
from statement import ReturnValue

class FunctionBase(CodeItemBase):

	argumentNames = ('datatype', 'name', 'args', 'locals', 'statementblock')
	passiveArguments = ('datatype', 'name', 'args', 'locals')

	saveVariables = True
	called = False
	hasStatementBlock = True

	def __init__(self, filename, line, *args):
		CodeItemBase.__init__(self, filename, line, *args)

		argdict = {}
		for arg in self.args:
			if '.' in arg.name:
				self.error("Illegal argument name: '.' is not allowed. Found '%s'" % arg.name)

			if arg.datatype == 'void':
				self.error("Illegal data type: 'void' is not a valid data type for arguments")

			if arg.name in argdict:
				self.error("Duplicate argument name: '%s'" % arg.name)

			argdict[arg.name] = arg

		self.argdict = argdict

		localdict = {}
		for local in self.locals:
			if '.' in local.name:
				self.error("Illegal local variable name: '.' is not allowed. Found '%s'" % local.name)

			if local.datatype == 'void':
				self.error("Illegal data type: 'void' is not a valid data type for local variables")

			if local.name in localdict or local.name in argdict:
				self.error("Duplicate variable name: '%s'" % local.name)

			localdict[local.name] = local

		self.localdict = localdict

	def getLocationForVariable(self, name):
		if name in self.argdict:
			return RegisterPointerOffset(C, self.args.index(self.argdict[name]) + 1)

		if name in self.localdict:
			return RegisterPointerOffset(C, -self.locals.index(self.localdict[name]))
		
		raise Exception("Internal error: unable to locate variable '%s' in function '%s'" % (name, self.name))

	def resolveIdentifiers(self, containingModule):
		if self.hasStatementBlock:
			CodeItemBase.resolveIdentifiers(self, containingModule)
		
		self.name = containingModule.name + '.' + self.name

	def registerIdentifiers(self, identifiers):
		self.identifiers = {}
		self.identifiers.update(identifiers)

		for arg in self.args:
			self.identifiers[arg.name] = arg

		for local in self.locals:
			self.identifiers[local.name] = local

	def transformToAsm(self):
		yield Instruction(Comment, 'start function')

		if self.saveVariables:
			yield Instruction(SET, Push(), C)

		yield Instruction(SET, C, SP())

		#if self.saveVariables:
		#	for i in xrange(len(self.args) + len(self.locals)):
		#		yield Instruction(SET, Push(), Registers[i + 2])

		#if (self.args):
		#	yield Instruction(Comment, 'read arguments')

		#for i in xrange(len(self.args)):
		#	yield Instruction(SET, Registers[i + 2], Pointer(i + ArgumentOffset))

		yield Instruction(SUB, SP(), Literal(len(self.locals)))

		for instruction in self.statementblock.transformToAsm(self, None):
			yield instruction

		# Register A now contains return value
			
		yield Instruction(Label, LabelReference('ret_' + self.name))
		yield Instruction(Comment, 'end function')

		yield Instruction(ADD, SP(), Literal(len(self.locals)))

		if self.saveVariables:
			yield Instruction(SET, C, Pop())

		#if self.saveVariables:
		#	for i in xrange(len(self.args) + len(self.locals) - 1, -1, -1):
		#		yield Instruction(SET, Registers[i + 2], Pop())

		if self.datatype != 'void':
			if not self.statementblock.statements or not isinstance(self.statementblock.statements[-1], ReturnValue):
				self.error("A value must be returned from functions with data type '%s'" % self.datatype)

	def stackUsage(self, functions):
		if self.saveVariables:
			return len(self.args) + len(self.locals) + self.statementblock.stackUsage(functions)
		return self.statementblock.stackUsage(functions)

class PredefinedFunction(FunctionBase):

	hasStatementBlock = False
	called = True

	def __init__(self, filename, line, name, asm, stackusage):
		FunctionBase.__init__(self, filename, line, 'void', name, [], [], None)

		self.asm = asm
		self.stackusage = stackusage

	def verifyIdentifiers(self, *args):
		pass

	def transformToAsm(self):
		yield Instruction(Label, LabelReference('func_' + self.name))

		for instruction in self.asm:
			yield instruction
	
	def stackUsage(self, functions):
		return self.stackusage

class Function(FunctionBase):

	def transformToAsm(self):
		yield Instruction(Label, LabelReference('func_' + self.name))

		for instruction in FunctionBase.transformToAsm(self):
			yield instruction

		yield Instruction(SET, PC(), Pop())

class MainFunction(Function):

	called = True
	saveVariables = False
