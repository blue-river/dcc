class Instruction(object):
	def __init__(self, opcode, a, b = None):
		self.opcode = opcode
		self.a = a
		self.b = b

	def size(self):
		if self.opcode == Comment or self.opcode == Label:
			return 0
		if self.opcode == JSR:
			return 1 + self.a.size()
		return 1 + self.a.size() + self.b.size()

	def asm(self):
		return self.opcode(self.a, self.b)

	def __repr__(self):
		return self.asm().strip()

def SET(a, b):
	return 'SET %s, %s' % (a.asm(), b.asm())
def ADD(a, b):
	return 'ADD %s, %s' % (a.asm(), b.asm())
def SUB(a, b):
	return 'SUB %s, %s' % (a.asm(), b.asm())
def MUL(a, b):
	return 'MUL %s, %s' % (a.asm(), b.asm())
def DIV(a, b):
	return 'DIV %s, %s' % (a.asm(), b.asm())
def MOD(a, b):
	return 'MOD %s, %s' % (a.asm(), b.asm())
def SHL(a, b):
	return 'SHL %s, %s' % (a.asm(), b.asm())
def SHR(a, b):
	return 'SHR %s, %s' % (a.asm(), b.asm())
def AND(a, b):
	return 'AND %s, %s' % (a.asm(), b.asm())
def BOR(a, b):
	return 'BOR %s, %s' % (a.asm(), b.asm())
def XOR(a, b):
	return 'XOR %s, %s' % (a.asm(), b.asm())
def IFE(a, b):
	return 'IFE %s, %s' % (a.asm(), b.asm())
def IFN(a, b):
	return 'IFN %s, %s' % (a.asm(), b.asm())
def IFG(a, b):
	return 'IFG %s, %s' % (a.asm(), b.asm())
def IFB(a, b):
	return 'IFB %s, %s' % (a.asm(), b.asm())

def JSR(a, b):
	return 'JSR %s' % a.asm()

def Comment(a, b):
	return '\n; %s' % a

def Label(a, b):
	return '\n\t:%s' % a.asm()


class Register(object):
	def __init__(self, register):
		self.register = register

	def size(self):
		return 0

	def asm(self):
		return self.register

A = Register('A')
B = Register('B')
C = Register('C')
X = Register('X')
Y = Register('Y')
Z = Register('Z')
I = Register('I')
J = Register('J')
Registers = A, B, C, X, Y, Z, I, J
TempStorage = A
RepeatCounter = B
ArgumentOffset = 0x4000 - 6

class SimpleValue(object):
	def size(self):
		return 0

class RegisterPointer(SimpleValue):
	def __init__(self, register):
		self.register = register

	def asm(self):
		return '[%s]' % self.register.register

class RegisterPointerOffset(object):
	def __init__(self, register, offset):
		self.register = register
		self.offset = offset

	def size(self):
		return 1

	def asm(self):
		return '[%d + %s]' % (self.offset, self.register.register)

class Pop(SimpleValue):
	def asm(self):
		return 'POP'

class Peek(SimpleValue):
	def asm(self):
		return 'PEEK'

class Push(SimpleValue):
	def asm(self):
		return 'PUSH'

class SP(SimpleValue):
	def asm(self):
		return 'SP'

class PC(SimpleValue):
	def asm(self):
		return 'PC'

class O(SimpleValue):
	def asm(self):
		return 'O'

class Pointer(object):
	def __init__(self, location):
		self.location = location

	def size(self):
		return 1

	def asm(self):
		return '[%s]' % self.location

class DataField(Pointer):
	def __init__(self, location):
		Pointer.__init__(self, dataFieldAddress(location))

class Literal(object):
	def __init__(self, value):
		self.value = value

	def size(self):
		if self.value < 0x20:
			return 1
		return 0

	def asm(self):
		return '%s' % self.value

class LabelReference(object):
	def __init__(self, name):
		self.name = name.replace('.', '__dot__')

	def size(self):
		return 1 # TODO

	def asm(self):
		return self.name


def count(program):
	instructions = 0
	codeBytes = 0
	realBytes = 0
	address = 0

	for instruction in program:
		#if instruction.type == 'origin':
		#	address = instruction.args[0]
		#	if realBytes < address:
		#		realBytes = address

		size = instruction.size()

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

	return LabelReference('%s_label_%X' % (name, thislabel))

memoryAddresses = {}
memoryAddress = 0x4000

def dataFieldAddress(dataField):
	global memoryAddress

	if dataField.constant:
		raise Exception('Internal error: cannot assign address to constant')

	if dataField.name not in memoryAddresses:
		if memoryAddress == 0x5000:
			# Use 0x5000 as an arbitrary limit. This allows for 4096 bytes of space.
			# Allowing more is not useful right now; more code memory would be required.
			dataField.error('Ran out of external address space for data fields!')

		memoryAddresses[dataField.name] = memoryAddress
		memoryAddress += 1

	return memoryAddresses[dataField.name]

def transform(datafields, functions):
	program = []

		#program.append(Asm('EQU', datafield.name, datafield.address))

	# stack pointer starts at the address of the last data field.
	# the stack data actually begins at the next address.

	#program.append(Asm('EQU', 'stack', stackStartAddress))

	#program += bootCode

	#program += initCode

	# TODO: do we need to null-initialize fields?

	#for datafield in datafields.values():
	#	if datafield.default is not None:
	#		if datafield.location == 'internal':
	#			program.append(Asm('MOV direct,#data', datafield.name, datafield.default))
	#		elif datafield.location == 'external':
	#			program.append(Asm('MOV DPTR,#data16', datafield.name))
	#			program.append(Asm('MOV direct,#data', 'ACC', datafield.default))
	#			program.append(Asm('MOVX @DPTR,A'))

	program += startCode

	for function in functions.values():
		index = len(program)
		program += function.transformToAsm()

	# 0 = maxStackSize
	return program, memoryAddress - 1

def programToAsm(program, options):
	lines = []
	codeAddressAliases = []

	comment = ''

	for instruction in program:
		if options.debugCodeGenerator:
			comment = ' ; %X' % instruction.address

		lines.append(instruction.asm())

	lines.append('\n')

	return '\n'.join(lines)

# data

#bootCode = [
#	Asm('origin', 0x00).addMetadataAfter('code address alias', 'boot code'),
#	Asm('AJMP addr11', 'init'),
#]

#initCode = [ 
#	Asm('origin', 0x80).addMetadataAfter('code address alias', 'initialisation'),
#	Asm('label', 'init'),
# Asm('MOV direct,#data', 'SP', 'stack'),
#]

#startCode = [
#	Asm('label', 'startcode'),
#	Asm('LCALL addr16', 'func_main__dot__main'),
#	Asm('label', 'mainexited').addMetadataAfter('code address alias', 'main exited'),
#	Asm('SJMP rel', 'mainexited'),
#]

startCode = [
	Instruction(Label, LabelReference('startcode')),
	Instruction(JSR, LabelReference('func_main__dot__main')),
	Instruction(Label, LabelReference('mainexited')),
	Instruction(SET, PC(), LabelReference('mainexited')),
]
