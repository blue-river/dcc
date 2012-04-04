from compiler import Asm
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

		if len(self.args) + len(self.locals) > 6:
			self.error("Function '%s' has %d arguments and local variables. At most 6 arguments and local variables are allowed" % (name, len(args) + len(locals)))

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

	def getRegisterForVariable(self, name):
		if name in self.argdict:
			return self.args.index(self.argdict[name]) + 2

		if name in self.localdict:
			return self.locals.index(self.localdict[name]) + len(self.args) + 2
		
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
		if self.saveVariables:
			for i in xrange(len(self.args) + len(self.locals)):
				yield Asm('PUSH direct', i + 2)

		for i in xrange(len(self.args)):
			yield Asm('MOV Rn,direct', i + 2, i + 0x08)

		for instruction in self.statementblock.transformToAsm(self, None):
			yield instruction
			
		yield Asm('label', 'ret_' + self.name)

		if self.saveVariables:
			for i in xrange(len(self.args) + len(self.locals) - 1, -1, -1):
				yield Asm('POP direct', i + 2)

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
		yield Asm('label', 'func_' + self.name)

		for instruction in self.asm:
			yield instruction
	
	def stackUsage(self, functions):
		return self.stackusage

class Function(FunctionBase):

	def transformToAsm(self):
		yield Asm('label', 'func_' + self.name)

		for instruction in FunctionBase.transformToAsm(self):
			yield instruction

		yield Asm('RET')

class MainFunction(Function):

	called = True
	saveVariables = False
