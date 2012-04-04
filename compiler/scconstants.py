from .data import sfr
from asmgenerator import Asm
from syntaxitems import DataField, Module, PredefinedFunction

def Constants():
	return {'sfr': SFRModule(), 'compilerservices': CompilerServicesModule()}

def CompilerServicesModule():
	functions = []

	functions.append(PredefinedFunction('compilerservices', 0, 'reti', (
			Asm('RETI'),
		), 0))

	functions.append(PredefinedFunction('compilerservices', 0, 'reset', (
			Asm('MOV direct,#data', 'SP', 'stack'),
			Asm('LJMP addr16', 'startcode'),
		), 0))

	return Module('compilerservices', 0, 'compilerservices', [], functions)

def SFRModule():
	datafields = []
	
	fakeLine = 0
	for sfrName in sfr.RegisterMapping:
		fakeLine += 1

		if sfr.RegisterMapping[sfrName][0] != 0:
			continue

		datafield = DataField('sfr', fakeLine, 'byte', sfrName)
		datafield.address = sfr.RegisterMapping[sfrName][1]
		datafield.location = 'internal'
		datafield.predefined = True
		datafields.append(datafield)
	
	return Module('sfr', 0, 'sfr', datafields, [])
