class Asm(object):

	def __init__(self, type, *args):
		self.type = type
		self.metadatabefore = []
		self.metadataafter = []

		if type == 'comment':
			self.args = args
		else:
			self.args = [replaceDot(arg) for arg in args]

	def addMetadataBefore(self, *args):
		self.metadatabefore.append(args)
		return self

	def addMetadataAfter(self, *args):
		self.metadataafter.append(args)
		return self

def replaceDot(arg):
	# hack
	if not isinstance(arg, str):
		return arg

	return arg.replace('.', '__dot__')

def count(program):
	instructions = 0
	codeBytes = 0
	realBytes = 0
	address = 0

	for instruction in program:
		if instruction.type == 'origin':
			address = instruction.args[0]

			if realBytes < address:
				realBytes = address

		size = AsmSize[instruction.type]

		instruction.address = address

		if size == 0:
			continue

		instructions += 1
		codeBytes += size
		realBytes += size
		address += size

	return instructions, codeBytes, realBytes

thislabel = -1

def nextlabel(name = 'unnamed'):
	global thislabel
	
	thislabel += 1

	return '%s_label_%X' % (name, thislabel)

def transform(datafields, functions):
	program = []
	memoryAddresses = {}

	internalMemoryAddress = 0x0E
	externalMemoryAddress = 0x4000

	for datafield in datafields.values():
		if datafield.constant:
			continue

		try:
			datafield.address
		except AttributeError:
			if datafield.location == 'internal':
				if internalMemoryAddress == 0x80:
					datafield.error('Ran out of internal address space for data fields!')

				datafield.address = internalMemoryAddress
				internalMemoryAddress += 1

				memoryAddresses[datafield.name] = ('internal', datafield.address)

			elif datafield.location == 'external':
				if externalMemoryAddress == 0x5000:
					# Use 0x5000 as an arbitrary limit. This allows for 4096 bytes of space.
					# Allowing more is not useful right now; more code memory would be required.
					datafield.error('Ran out of external address space for data fields!')

				datafield.address = externalMemoryAddress
				externalMemoryAddress += 1

				memoryAddresses[datafield.name] = ('external', datafield.address)
			else:
				raise Exception("Internal error: Unknown data field location '%s'" % datafield.location)

		program.append(Asm('EQU', datafield.name, datafield.address))

	# stack pointer starts at the address of the last data field.
	# the stack data actually begins at the next address.
	stackStartAddress = internalMemoryAddress - 1

	maxStackSize = 0xFF - stackStartAddress

	program.append(Asm('EQU', 'stack', stackStartAddress))

	program += bootCode

	for vectorName in InterruptVectors:
		ihName = 'interrupts.handler_%s' % vectorName
		if ihName in functions:
			vectorDebugName = 'interrupt vector %s' % vectorName
			program.append(Asm('origin', InterruptVectors[vectorName]))
			program.append(Asm('LJMP addr16', 'func_' + ihName).addMetadataBefore('code address alias', vectorDebugName))
	program += initCode

	for datafield in datafields.values():
		if datafield.default is not None:
			if datafield.location == 'internal':
				program.append(Asm('MOV direct,#data', datafield.name, datafield.default))
			elif datafield.location == 'external':
				program.append(Asm('MOV DPTR,#data16', datafield.name))
				program.append(Asm('MOV direct,#data', 'ACC', datafield.default))
				program.append(Asm('MOVX @DPTR,A'))

	program += startCode

	for function in functions.values():
		index = len(program)
		program += function.transformToAsm()
		program[index].addMetadataAfter('code address alias', function.name)

	debugData = {'memoryAddresses': memoryAddresses}

	return program, maxStackSize, internalMemoryAddress - 1, externalMemoryAddress - 1, debugData

def programToAsm(program, options):
	lines = []
	codeAddressAliases = []

	def processMetadata(asm, metadataList, after):
		for metadata in metadataList:
			if metadata[0] == 'comment':
				lines.append('; ' + metadata[1])

			elif metadata[0] == 'code address alias':
				address = asm.address

				if after:
					address += AsmSize[asm.type]

				codeAddressAliases.append((asm.address, metadata[1]))

			else:
				raise Exception("Internal error: unknown metadata type '%s'" % metadata[0])

	comment = ''

	for asm in program:
		processMetadata(asm, asm.metadatabefore, after=False)

		if options.debugCodeGenerator:
			comment = ' ; %X' % asm.address

		lines.append('\t' + AsmOutput[asm.type] % tuple(asm.args) + comment)

		processMetadata(asm, asm.metadataafter, after=True)

	debugData = {'codeAddressAliases': codeAddressAliases}

	lines.append('\n')

	return '\n'.join(lines), debugData

# data

bootCode = [
	Asm('origin', 0x00).addMetadataAfter('code address alias', 'boot code'),
	Asm('AJMP addr11', 'init'),
]

initCode = [ 
	Asm('origin', 0x80).addMetadataAfter('code address alias', 'initialisation'),
	Asm('label', 'init'),
	Asm('MOV direct,#data', 'SP', 'stack'),
]

startCode = [
	Asm('label', 'startcode'),
	Asm('LCALL addr16', 'func_main__dot__main'),
	Asm('label', 'mainexited').addMetadataAfter('code address alias', 'main exited'),
	Asm('SJMP rel', 'mainexited'),
]

AsmOutput = {
	'origin': '\nORG 0x%X',
	'label': '\n%s:',
	'EQU': '%s EQU 0x%X',
	'comment': '; %s',

	'ACALL addr11': 'ACALL %s',
	'ADD A,Rn': 'ADD A,R%d',
	'AJMP addr11': 'AJMP %s',
	'ANL A,Rn': 'ANL A,R%d',
	'CJNE A,direct,rel': 'CJNE A,%s,%s',
	'CJNE Rn,#data,rel': 'CJNE R%d,#%s,%s',
	'CLR bit': 'CLR %s.%d',
	'CLR C': 'CLR C',
	'CPL A': 'CPL A',
	'CPL bit': 'CPL %s.%d',
	'DEC direct': 'DEC %s',
	'DJNZ Rn,rel': 'DJNZ R%d,%s',
	'INC direct': 'INC %s',
	'JB bit,rel': 'JB %s.%d,%s',
	'JC rel': 'JC %s',
	'JNB bit,rel': 'JNB %s.%d,%s',
	'JZ rel': 'JZ %s',
	'LCALL addr16': 'LCALL %s',
	'LJMP addr16': 'LJMP %s',
	'MOV A,#data': 'MOV A,#%s',
	'MOV A,Rn': 'MOV A,R%d',
	'MOV A,direct': 'MOV A,%s',
	'MOV C,bit': 'MOV C,%s.%d',
	'MOV DPTR,#data16': 'MOV DPTR,#%s',
	'MOV Rn,#data': 'MOV R%d,#%s',
	'MOV Rn,direct': 'MOV R%d,%s',
	'MOV bit,C': 'MOV %s.%d,C',
	'MOV direct,#data': 'MOV %s,#%s',
	'MOV direct,A': 'MOV %s,A',
	'MOV direct,Rn': 'MOV %s,R%d',
	'MOV direct,direct': 'MOV %s,%s',
	'MOVX @DPTR,A': 'MOVX @DPTR,A',
	'MOVX A,@DPTR': 'MOVX A,@DPTR',
	'MUL AB': 'MUL AB',
	'ORL A,Rn': 'ORL A,R%d',
	'POP direct': 'POP %s',
	'PUSH direct': 'PUSH %s',
	'SETB bit': 'SETB %s.%d',
	'SJMP rel': 'SJMP %s',
	'SUBB A,Rn': 'SUBB A,R%d',
	'RET': 'RET',
	'RETI': 'RETI',
	'XRL A,Rn': 'XRL A,R%d',
}

AsmSize = {
	'origin': 0,
	'label': 0,
	'EQU': 0,
	'comment': 0,

	'ACALL addr11': 2,
	'ADD A,Rn': 1,
	'AJMP addr11': 2,
	'ANL A,Rn': 1,
	'CJNE A,direct,rel': 3,
	'CJNE Rn,#data,rel': 3,
	'CLR C': 1,
	'CLR bit': 2,
	'CPL A': 1,
	'CPL bit': 2,
	'DEC direct': 2,
	'DJNZ Rn,rel': 2,
	'INC direct': 2,
	'JB bit,rel': 3,
	'JC rel': 2,
	'JNB bit,rel': 3,
	'JZ rel': 2,
	'LCALL addr16': 3,
	'LJMP addr16': 3,
	'MOV A,#data': 2,
	'MOV A,Rn': 1,
	'MOV A,direct': 2,
	'MOV C,bit': 2,
	'MOV DPTR,#data16': 3,
	'MOV Rn,#data': 2,
	'MOV Rn,direct': 2,
	'MOV bit,C': 2,
	'MOV direct,#data': 3,
	'MOV direct,A': 2,
	'MOV direct,Rn': 2,
	'MOV direct,direct': 3,
	'MOVX @DPTR,A': 1,
	'MOVX A,@DPTR': 1,
	'MUL AB': 1,
	'ORL A,Rn': 1,
	'POP direct': 2,
	'PUSH direct': 2,
	'SETB bit': 2,
	'SJMP rel': 2,
	'SUBB A,Rn': 1,
	'RET': 1,
	'RETI': 1,
	'XRL A,Rn': 1,
}

InterruptVectors = {
	'IE0': 0x03,
	'TF0': 0x0B,
	'IE1': 0x13,
	'TF1': 0x1B,
	'RI_TI': 0x23,
	'TF2': 0x2B,
	'IADC': 0x43,
	'IE2': 0x4B,
	'TRF_BCERR': 0x53,
	'CT2P': 0x5B,
	'CCnF_CCnR': 0x63,
	'CT1FP_CT1FC': 0x6B,
	'PDI': 0x7B,
}

