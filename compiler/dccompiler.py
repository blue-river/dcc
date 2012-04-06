import os.path

import json

from asmoptimizer import AsmOptimizer
from compilererror import CompilerError
from dcconstants import Constants
from dcparser import DCParser
import asmgenerator

class DCCompiler(object):

	def compile(self, options):
		modules = Constants() # dict
		nextModules = set(['main'])

		for path in options.moduleSearchPath:
			if not os.path.isdir(path):
				raise CompilerError(None, None, "Module search path '%s' does not exist" % path)
				
		while nextModules:
			nextModule = nextModules.pop()
			if nextModule in modules:
				continue

			if options.verboseprogress:
				print 'Parsing module %s...' % nextModule

			modules[nextModule], foundModuleReferences = self.parse(options, nextModule)
			nextModules.update(foundModuleReferences)

		if options.verboseprogress:
			print 'Resolving identifiers...'
			
		self.resolveIdentifiers(modules)

		datafields, functions = self.merge(modules)

		self.registerIdentifiers(datafields, functions)

		self.verifyIdentifiers(datafields, functions)

		self.checkIdentifierUsage(datafields, functions)

		if options.optimize and False:
			if options.verboseprogress:
				print 'Optimizing source...'

			self.optimizeSyntaxTree(datafields, functions)

		print 'Max stack usage: %d bytes' % (functions['main.main'].stackUsage(functions) + 2)

		if options.optimize:
			print 'Note: stack usage could be less, because optimization is enabled'

		if options.verboseprogress:
			print 'Generating assembly...'

		program, maxStackSize, memoryEndAddress = asmgenerator.transform(datafields, functions)

		if options.optimize:
			if options.verboseprogress:
				print 'Optimizing assembly...'

			self.optimizeAsm(options, program)

		if not options.verboseinfo or not options.verboseprogress:
			self.printAsmStatistics(program)

		self.checkCodeSize(program)

		print 'Stack space available: %d bytes' % maxStackSize

		if options.verboseinfo:
			if memoryEndAddress >= 0x4000:
				print 'Memory used: 0x4000-0x%X' % memoryEndAddress

		asm = asmgenerator.programToAsm(program, options)

		return asm
		

	def parse(self, options, modulename):
		'''Parses the input and returns a syntax tree.'''

		filename = modulename + '.dc'

		inputFile = None
		if os.path.isfile(filename):
			inputFile = open(filename)
		else:
			for modulePath in options.moduleSearchPath:
				path = '%s%s%s' % (modulePath, os.sep, filename)
				if os.path.isfile(path):
					inputFile = open(path)
					break

		if not inputFile:
			raise CompilerError(None, None, "Module '%s' not found in search path" % modulename)

		input = inputFile.read()
		inputFile.close()

		return DCParser(options).parse(filename, modulename, input)

	def printAsmStatistics(self, program):
		instructions, codeBytes, realBytes = asmgenerator.count(program)
		print "Program size: %s words (%s code words, %s instructions)" % (realBytes, codeBytes, instructions)

	def checkCodeSize(self, program):
		ignore, ignore, realBytes = asmgenerator.count(program)
		if realBytes > 0x4000:
			raise Exception('Internal error: Code size exceeds 0x4000 words, would overlap with external data fields')

	def checkIdentifierUsage(self, datafields, functions):
		for datafield in datafields.values():
			if datafield.predefined:
				continue

			if not datafield.assigned and not datafield.read:
				print "Warning: data field '%s' is never used" % datafield.name
			elif not datafield.assigned:
				print "Warning: data field '%s' is never assigned" % datafield.name
			elif not datafield.read:
				print "Warning: data field '%s' is never read" % datafield.name

		for function in functions.values():
			if not function.called:
				print "Warning: function '%s' is never called" % function.name

		# TODO: local variables

	def resolveIdentifiers(self, modules):
		'''Changes identifiers to their full name and generates an error for unresolvable identifiers.'''
		modulesDict = {}

		for module in modules.values():
			module.resolveIdentifiers()

	def merge(self, modules):
		'''Merges the modules and returns the combined data fields and functions.'''

		datafields = {}
		functions = {}

		for module in modules.values():
			for datafield in module.datafields:
				if datafield.name in datafields:
					self.duplicateError(datafields[datafield.name], datafield)

				datafields[datafield.name] = datafield

			for function in module.functions:
				if function.name in functions:
					self.duplicateError(functions[function.name], function)

				if function.name in datafields:
					self.duplicateError(function, datafields[function.name])

				functions[function.name] = function

		return (datafields, functions)

	def duplicateError(self, left, right):
		if left.line > right.line:
			high = left
			low = right
		else:
			high = right
			low = left

		high.error("'%s' redefined (previous definition on line %d)" % (high.name, low.line))

	def verifyIdentifiers(self, datafields, functions):
		'''Verifies that all identifiers are valid, and generates an error if they are not.'''

		for function in functions.values():
			function.verifyIdentifiers(datafields, functions, function)

			if function.name == 'main.main':
				if len(function.args) != 0:
					function.error('The main function cannot have arguments.')
				# TODO: check return type == void

		if 'main.main' not in functions:
			raise CompilerError(None, None, "No 'main' module with 'main' function found")

	def registerIdentifiers(self, datafields, functions):
		'''Provides the identifier list to the functions.'''

		identifiers = {}
		identifiers.update(datafields)
		identifiers.update(functions)

		if len(identifiers) != len(datafields) + len(functions):
			raise Exception('Internal error: %d != %d + %d' % (len(identifiers), len(datafields), len(functions)))

		for function in functions.values():
			function.registerIdentifiers(identifiers)

	def optimizeSyntaxTree(self, datafields, functions):
		for function in functions.values():
			function.optimize()

	def optimizeAsm(self, options, program):
		optimizer = AsmOptimizer(program, options)

		if options.verboseinfo and options.verboseprogress:
			self.printAsmStatistics(program)

		while optimizer.doPass():
			if options.verboseinfo and options.verboseprogress:
				self.printAsmStatistics(program)

		if options.verboseprogress:
			print 'Assembly optimized.'
