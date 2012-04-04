import cmd
import json

try:
	import readline
except ImportError:
	pass

from lib.asmdecoder import AsmDecoder
from lib.uploadprogram import uploadProgram

def run(hardware):
	cli = CommandLineInterface(hardware)
	cli.printStatus()
	cli.cmdloop()

class CommandLineInterface(cmd.Cmd):
	def __init__(self, hardware, *args, **kwargs):
		cmd.Cmd.__init__(self, *args, **kwargs)
		self.hardware = hardware
		self.asmdecoder = AsmDecoder(hardware)
		self.running = False

		self.codeAddressAliases = []
		self.codeAddressAliasesDict = {}
		self.memoryAddresses = {}

	def printStatus(self):
		reg = self.hardware.getRegisters()

		pc = reg[12] << 8 | reg[13]

		print
		print '  A: %02X   B: %02X  SP: %02X' % (reg[0], reg[1], reg[18]<< 8 | reg[19])
		print ' R0: %02X  R2: %02X  R4: %02X  R6: %02X' % (reg[2], reg[4], reg[6], reg[8])
		print ' R1: %02X  R3: %02X  R5: %02X  R7: %02X' % (reg[3], reg[5], reg[7], reg[9])
		print 'PSW: %02X (%s)  DPTR: %04X' % (reg[14], self.parsePSW(reg[14]), reg[10] << 8 | reg[11])
		print 'Unknown: %02X %02X %02X %02X' % (reg[15], reg[16], reg[17], reg[20])

		self.asmdecoder.markVisited(pc)

		print
		print 'PC = %04X (%s)' % (pc, self.asmdecoder.getStringForAddress(pc))
		address, mnemonic = self.asmdecoder.getMnemonic(pc)
		self.printInstruction(address, mnemonic, pc, showAlias=False)

	def parsePSW(self, psw):
		if psw & 0b10000000:
			cy = 'C'
		else:
			cy = '-'
		
		if psw & 0b01000000:
			ac = 'A'
		else:
			ac = '-'

		if psw & 0b00100000:
			f0 = '*'
		else:
			f0 = '-'

		rs = (psw & 0b00011000) >> 3

		if psw & 0b00000100:
			ov = 'O'
		else:
			ov = '-'

		if psw & 0b00000010:
			f1 = '*'
		else:
			f1 = '-'

		if psw & 0b00000001:
			p = 'P'
		else:
			p = '-'

		return '%s%s%s%s%s%s%s' % (cy, ac, f0, rs, ov, f1, p)


	def printInstruction(self, address, mnemonic, pc, showAlias=True):
		joined = ' '.join((mnemonic[0], ', '.join(mnemonic[1:])))

		if address == pc:
			marker = '-->'
		else:
			marker = '   '

		if showAlias and address in self.codeAddressAliasesDict:
			print '   (%s)' % self.codeAddressAliasesDict[address]

		print '%s %04X: %s' % (marker, address, joined)

	def do_list(self, line):
		'''Shows the previous, current and next instructions located around the specified
address. (Default: program counter)'''

		if self.running:
			print 'Program is running. Stop execution to issue commands.'
			return

		instructions = []

		
		pc = self.hardware.getPC()

		if line:
			target = int(line, 16)
		else:
			target = self.hardware.getPC()
		address = target - 1

		for i in xrange(5):
			address, mnemonic = self.asmdecoder.getMnemonic(address, direction=-1)
			instructions.insert(0, (address, mnemonic))

			address -= 1

		address = target
		for i in xrange(6):
			address, mnemonic = self.asmdecoder.getMnemonic(address)
			instructions.append((address, mnemonic))

			address += 1

		for address, mnemonic in instructions:
			self.printInstruction(address, mnemonic, pc)

	def do_show(self, line):
		'''Shows contents of a variable.
Syntax: show <variable>'''

		if self.running:
			print 'Program is running. Stop execution to issue commands.'
			return

		if line not in self.memoryAddresses:
			print "Variable '%s' not found." % line
			return

		address = self.memoryAddresses[line]
		if address[0] == 'internal':
			mem = self.hardware.readDirect(address[1], 0x01)
		elif address[0] == 'external':
			mem = self.hardware.readExternal(address[1], 0x01)

		print '%04X  %02X' % (address[1], mem[0])

	def do_mem(self, line):
		'''Shows memory contents.
Syntax: mem <type> <address>
type can be one of: direct indirect external code (may be abbreviated)
mem shows a block of size 0x20 containing the specified address.'''

		if self.running:
			print 'Program is running. Stop execution to issue commands.'
			return

		parts = [part for part in line.split(' ') if part]

		if len(parts) != 2 or parts[0][0] not in ('d', 'i', 'e', 'c'):
			print 'syntax: mem <type> <address>'
			print 'type can be one of: direct indirect external code (may be abbreviated)'

		address = int(parts[1], 16) & 0xffe0
		
		if parts[0][0] == 'd':
			mem = self.hardware.readDirect(address, 0x20)
		elif parts[0][0] == 'i':
			mem = self.hardware.readIndirect(address, 0x20)
		elif parts[0][0] == 'e':
			mem = self.hardware.readExternal(address, 0x20)
		elif parts[0][0] == 'c':
			mem = self.hardware.readCode(address, 0x20)

		print ('%04X ' + ' %02X' * 8) % ((address, ) + tuple(mem[0:8]))
		print ('%04X ' + ' %02X' * 8) % ((address + 8, ) + tuple(mem[8:16]))
		print ('%04X ' + ' %02X' * 8) % ((address + 16, ) + tuple(mem[16:24]))
		print ('%04X ' + ' %02X' * 8) % ((address + 24, ) + tuple(mem[24:32]))

	def do_step(self, line):
		'Executes the specified number of instructions. (Default: 1)'

		if self.running:
			print 'Program is running. Stop execution to issue commands.'
			return

		steps = 1

		if line:
			steps = int(line)

		while steps:
			self.hardware.step()
			steps -= 1

		self.printStatus()

	def do_load(self, line):
		'''Uploads a program to the hardware.
Syntax: load <path-to-hexfile>'''

		if self.running:
			print 'Program is running. Stop execution to issue commands.'
			return

		if line[-4:] == '.hex':
			line = line[:-4]

		try:
			with open(line + '.hex') as inputFile:
				prog = inputFile.read()
		except IOError, e:
			print "Error reading '%s.hex': %s" % (line, e)
			return

		uploadProgram(prog, self.hardware)

		self.do_loadDebug(line)
		self.asmdecoder.invalidateCache()
		self.asmdecoder.markVisited(self.hardware.getPC())


		self.printStatus()

	def do_loaddebug(self, line):
		'''Loads debug information for a program.
Syntax: loaddebug <path-to-scdebugfile>'''

		debugData = {'codeAddressAliases': None, 'memoryAddresses': None}

		try:
			with open(line + '.scdebug') as inputFile:
				debugData = json.load(inputFile)
		except IOError, e:
			print "Error reading '%s.scdebug': %s" % (line, e)
			return

		if line[-8:] == '.scdebug':
			line = line[:-8]

		self.codeAddressAliases = debugData['codeAddressAliases']
		self.asmdecoder.addressAliases = self.codeAddressAliases

		self.codeAddressAliasesDict = dict(self.codeAddressAliases)
		
		self.memoryAddresses = debugData['memoryAddresses']

	def do_run(self, line):
		'''Resumes execution of the program.
go disables all commands and enables stop.'''

		if self.running:
			print 'Program is running. Stop execution to issue commands.'
			return

		self.running = True
		self.hardware.run()

	def do_stop(self, line):
		if not self.running:
			print "Can't stop. Program is not running."
			return

		self.hardware.stop()
		self.running = False
		self.printStatus()

	def do_reset(self, line):
		if self.running:
			print 'Program is running. Stop execution to issue commands.'
			return

		self.hardware.reset()
		self.printStatus()

	def do_exit(self, line):
		'Quits the debugger.'
		return True

	def emptyline(self):
		pass

	def do_EOF(self, line):
		print
		return self.do_exit(line)

#	def postcmd
