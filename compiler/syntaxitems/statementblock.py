from codeitembase import CodeItemBase

class StatementBlock(CodeItemBase):

	argumentNames = ('statements', )
	passiveArguments = ('statements', )

	def resolveIdentifiers(self, containingModule):
		CodeItemBase.resolveIdentifiers(self, containingModule)

		for statement in self.statements:
			statement.resolveIdentifiers(containingModule)

	def verifyIdentifiers(self, datafields, functions, containingFunction):
		CodeItemBase.verifyIdentifiers(self, datafields, functions, containingFunction)

		for statement in self.statements:
			statement.verifyIdentifiers(datafields, functions, containingFunction)

	def transformToAsm(self, containingFunction, containingLoop):
		for statement in self.statements:
			for instruction in statement.transformToAsm(containingFunction, containingLoop):
				yield instruction

	def optimize(self):
		for i in xrange(len(self.statements)):
			self.statements[i] = self.statements[i].optimize()

		return self

	def stackUsage(self, functions):
		if not self.statements:
			return 0

		return max(statement.stackUsage(functions) for statement in self.statements)
