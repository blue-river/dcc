from asmgenerator import *
from syntaxitems import DataField, Module, PredefinedFunction

def Constants():
	return {'compilerservices': CompilerServicesModule()}

def CompilerServicesModule():
	functions = []

	functions.append(PredefinedFunction('compilerservices', 0, 'reset', (
			Instruction(SET, SP(), Literal(0)),
			Instruction(SET, PC(), Literal(0)),
		), 0))

	return Module('compilerservices', 0, 'compilerservices', [], functions)
