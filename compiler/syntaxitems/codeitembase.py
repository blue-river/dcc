from abstractsyntaxitem import AbstractSyntaxItem

class CodeItemBase(AbstractSyntaxItem):
	'''
	The base class for all code-generating syntax items.

	Subclasses must expose the following attributes:
	* argumentNames
	    A sequence of argument names required by the syntax item.

	Subclasses may expose the following attributes:
	* passiveArguments
	    A set of names of arguments which are not syntax items.
		resolveIdentifiers and verifyIdentifiers will be called on all arguments,
		except those specified by passiveArguments.

	Subclasses may override the following functions:
	* resolveIdentifiers
	    Override when the syntax item directly contains an identifier which must
		be resolved, or the arguments need special handling.
	* verifyIdentifiers
		Override when the syntax item directly contains an identifier, or the
		arguments need special handling.
	* optimize
	    Replace the contained syntax tree with a more efficient version.
		Return a new object if self needs to be replaced with another object,
		otherwise return self.

	Subclasses must implement the following functions:
	* transformToAsm
		Returns a sequence of Asm instances that perform the syntax item's action.
	'''

	passiveArguments = ()

	def __init__(self, filename, line, *args):
		AbstractSyntaxItem.__init__(self, filename, line)

		if len(args) != len(self.argumentNames):
			self.error("Internal error: incorrect number of arguments for code item '%s'. Expected %d, got %d" % (type(self).__name__, len(self.argumentNames), len(args)))

		for index in xrange(len(self.argumentNames)):
			setattr(self, self.argumentNames[index], args[index])

	def resolveIdentifiers(self, containingModule):
		'''
		Resolves unqualified identifiers to their containing module.

		This only changes function identifiers. Variables are always fully qualified,
		and local variables are not qualified.
		'''
		
		for argument in self.argumentNames:
			if argument not in self.passiveArguments:
				getattr(self, argument).resolveIdentifiers(containingModule)

		self.containingModule = containingModule.name

	def verifyIdentifiers(self, datafields, functions, containingFunction):
		'''Verifies that identifiers actually exist.'''

		for argument in self.argumentNames:
			if argument not in self.passiveArguments:
				getattr(self, argument).verifyIdentifiers(datafields, functions, containingFunction)

	def optimize(self):
		for argument in self.argumentNames:
			if argument not in self.passiveArguments:
				setattr(self, argument, getattr(self, argument).optimize())

		return self
