class AsmDecoder(object):

	TYPE_UNKNOWN = object()
	TYPE_INSTRUCTION = object()
	TYPE_MULTIBYTE = object()

	def __init__(self, memory):
		self.memory = memory

		self.addressAliases = []

		self.invalidateCache()

	def invalidateCache(self):
		self.cache = [(self.TYPE_UNKNOWN, None)] * 65536

		for addr, ignored in self.addressAliases:
			self.markVisited(addr)

	def markVisited(self, address):
		self.cache[address] = (self.TYPE_INSTRUCTION, self.cache[address][1])

	def getStringForAddress(self, address):
		lastAlias = '0'
		lastAddr = 0

		for addr, alias in self.addressAliases:
			if address < addr:
				return lastAlias + '+%X' % (address - lastAddr)

			lastAlias = alias
			lastAddr = addr

		return lastAlias + '+%X' % (address - lastAddr)

	def getMnemonic(self, address, direction=1):
		if address > 0xf000:
			address -= 0x10000

		while self.cache[address][0] is self.TYPE_MULTIBYTE:
			address += direction

		self.ensureCached(address % 0x10000)

		if self.cache[address][0] is self.TYPE_UNKNOWN:
			return address % 0x10000, ('DB', '%03Xh' % self.cache[address][1])

		length = 1
		mnemonic = []

		for part in self.opcodes[self.cache[address][1]]:
			if part == 'direct':
				part = '%03Xh' % self.cache[address + length][1]
				length += 1
			elif part == '#data':
				part = '#%03Xh' % self.cache[address + length][1]
				length += 1
			elif part == '#data16':
				part = '#%05Xh' % (self.cache[address + length][1] << 8 | self.cache[address + length + 1][1])
				length += 2
			elif part == 'rel':
				targetAddress = self.readRel(self.cache[address + length][1]) + address + length + 1
				part = '%05Xh' % targetAddress
				self.markVisited(targetAddress)
				length += 1
			elif part == '/bit':
				byte, bit = self.decodeBit(self.cache[address + length][1])
				part = '/%03Xh.%d' % (byte, bit)
				length += 1
			elif part == 'bit':
				byte, bit = self.decodeBit(self.cache[address + length][1])
				part = '%03Xh.%d' % (byte, bit)
				length += 1
			elif part == 'addr11':
				targetAddress = self.readAddr11(self.cache[address][1], self.cache[address + length][1]) | (address & (0x11111 << 11))
				part = '%05Xh' % targetAddress
				self.markVisited(targetAddress)
				length += 1
			elif part == 'addr16':
				targetAddress = self.cache[address + length][1] << 8 | self.cache[address + length + 1][1]
				part = '%05Xh' % targetAddress
				self.markVisited(targetAddress)
				length += 2

			mnemonic.append(part)

		for offset in xrange(1,length):
			self.cache[address + offset] = (self.TYPE_MULTIBYTE, self.cache[address + offset][1])

		if mnemonic[0] not in self.unreachableAfter:
			self.cache[address + length] = (self.TYPE_INSTRUCTION, self.cache[address + length][1])

		return address % 0x10000, mnemonic

	def decodeBit(self, inByte):
		if inByte < 0x80:
			return (inByte >> 3) + 0x20, inByte & 0x7
		else:
			return inByte & 0xf8, inByte & 0x7

	def readRel(self, byte):
		if byte < 0x80:
			return byte

		return byte - 0x100

	def readAddr11(self, opcode, byte):
		return ((opcode >> 5) << 8) | byte

	def ensureCached(self, address):
		if self.cache[address][1] is None:
			self.populateCache(address)
		if self.cache[(address + 2) % 0x10000][1] is None:
			self.populateCache((address + 2) % 0x10000)

	def populateCache(self, address):
		address -= address % 0x20

		bytes = self.memory.readCode(address, 0x20)
		for byte in bytes:
			self.cache[address] = (self.cache[address][0], byte)
			address += 1

	def parse(self, opcode):
		generic = parseGeneric(opcode)

		if generic:
			return generic

		return parseSpecific(opcode)

	unreachableAfter = (
		'AJMP',
		'LJMP',
		'RET',
		'RETI',
		'SJMP',
	)

	opcodes = (
		# 00
		('NOP',),
		('AJMP', 'addr11'),
		('LJMP', 'addr16'),
		('RR', 'A'),
		('INC', 'A'),
		('INC', 'direct'),
		('INC', '@R0'),
		('INC', '@R1'),
		('INC', 'R0'),
		('INC', 'R1'),
		('INC', 'R2'),
		('INC', 'R3'),
		('INC', 'R4'),
		('INC', 'R5'),
		('INC', 'R6'),
		('INC', 'R7'),

		# 10
		('JBC', 'bit', 'rel'),
		('ACALL', 'addr11'),
		('LCALL', 'addr16'),
		('RRC', 'A'),
		('DEC', 'A'),
		('DEC', 'direct'),
		('DEC', '@R0'),
		('DEC', '@R1'),
		('DEC', 'R0'),
		('DEC', 'R1'),
		('DEC', 'R2'),
		('DEC', 'R3'),
		('DEC', 'R4'),
		('DEC', 'R5'),
		('DEC', 'R6'),
		('DEC', 'R7'),

		# 20
		('JB', 'bit', 'rel'),
		('AJMP', 'addr11'),
		('RET',),
		('RL', 'A'),
		('ADD', 'A', '#data'),
		('ADD', 'A', 'direct'),
		('ADD', 'A', '@R0'),
		('ADD', 'A', '@R1'),
		('ADD', 'A', 'R0'),
		('ADD', 'A', 'R1'),
		('ADD', 'A', 'R2'),
		('ADD', 'A', 'R3'),
		('ADD', 'A', 'R4'),
		('ADD', 'A', 'R5'),
		('ADD', 'A', 'R6'),
		('ADD', 'A', 'R7'),

		# 30
		('JNB', 'bit', 'rel'),
		('ACALL', 'addr11'),
		('RETI',),
		('RLC', 'A'),
		('ADDC', 'A', '#data'),
		('ADDC', 'A', 'direct'),
		('ADDC', 'A', '@R0'),
		('ADDC', 'A', '@R1'),
		('ADDC', 'A', 'R0'),
		('ADDC', 'A', 'R1'),
		('ADDC', 'A', 'R2'),
		('ADDC', 'A', 'R3'),
		('ADDC', 'A', 'R4'),
		('ADDC', 'A', 'R5'),
		('ADDC', 'A', 'R6'),
		('ADDC', 'A', 'R7'),

		# 40
		('JC', 'rel'),
		('AJMP', 'addr11'),
		('ORL', 'direct', 'A'),
		('ORL', 'direct', '#data'),
		('ORL', 'A', '#data'),
		('ORL', 'A', 'direct'),
		('ORL', 'A', '@R0'),
		('ORL', 'A', '@R1'),
		('ORL', 'A', 'R0'),
		('ORL', 'A', 'R1'),
		('ORL', 'A', 'R2'),
		('ORL', 'A', 'R3'),
		('ORL', 'A', 'R4'),
		('ORL', 'A', 'R5'),
		('ORL', 'A', 'R6'),
		('ORL', 'A', 'R7'),

		# 50
		('JNC', 'rel'),
		('ACALL', 'addr11'),
		('ANL', 'direct', 'A'),
		('ANL', 'direct', '#data'),
		('ANL', 'A', '#data'),
		('ANL', 'A', 'direct'),
		('ANL', 'A', '@R0'),
		('ANL', 'A', '@R1'),
		('ANL', 'A', 'R0'),
		('ANL', 'A', 'R1'),
		('ANL', 'A', 'R2'),
		('ANL', 'A', 'R3'),
		('ANL', 'A', 'R4'),
		('ANL', 'A', 'R5'),
		('ANL', 'A', 'R6'),
		('ANL', 'A', 'R7'),

		# 60
		('JZ', 'rel'),
		('AJMP', 'addr11'),
		('XRL', 'direct', 'A'),
		('XRL', 'direct', '#data'),
		('XRL', 'A', '#data'),
		('XRL', 'A', 'direct'),
		('XRL', 'A', '@R0'),
		('XRL', 'A', '@R1'),
		('XRL', 'A', 'R0'),
		('XRL', 'A', 'R1'),
		('XRL', 'A', 'R2'),
		('XRL', 'A', 'R3'),
		('XRL', 'A', 'R4'),
		('XRL', 'A', 'R5'),
		('XRL', 'A', 'R6'),
		('XRL', 'A', 'R7'),

		# 70
		('JNZ', 'rel'),
		('ACALL', 'addr11'),
		('ORL', 'C', 'direct'),
		('JMP', '@A+DPTR'),
		('MOV', 'A', '#data'),
		('MOV', 'direct', '#data'),
		('MOV', '@R0', '#data'),
		('MOV', '@R1', '#data'),
		('MOV', 'R0', '#data'),
		('MOV', 'R1', '#data'),
		('MOV', 'R2', '#data'),
		('MOV', 'R3', '#data'),
		('MOV', 'R4', '#data'),
		('MOV', 'R5', '#data'),
		('MOV', 'R6', '#data'),
		('MOV', 'R7', '#data'),

		# 80
		('SJMP', 'rel'),
		('AJMP', 'addr11'),
		('ANL', 'C', 'bit'),
		('MOVC', 'A', '@A+PC'),
		('DIV', 'AB'),
		('MOV', 'direct', 'direct'),
		('MOV', 'direct', '@R0'),
		('MOV', 'direct', '@R1'),
		('MOV', 'direct', 'R0'),
		('MOV', 'direct', 'R1'),
		('MOV', 'direct', 'R2'),
		('MOV', 'direct', 'R3'),
		('MOV', 'direct', 'R4'),
		('MOV', 'direct', 'R5'),
		('MOV', 'direct', 'R6'),
		('MOV', 'direct', 'R7'),

		# 90
		('MOV', 'DPTR', '#data16'),
		('ACALL', 'addr11'),
		('MOV', 'bit', 'C'),
		('MOVC', 'A', '@A+DPTR'),
		('SUBB', 'A', '#data'),
		('SUBB', 'A', 'direct'),
		('SUBB', 'A', '@R0'),
		('SUBB', 'A', '@R1'),
		('SUBB', 'A', 'R0'),
		('SUBB', 'A', 'R1'),
		('SUBB', 'A', 'R2'),
		('SUBB', 'A', 'R3'),
		('SUBB', 'A', 'R4'),
		('SUBB', 'A', 'R5'),
		('SUBB', 'A', 'R6'),
		('SUBB', 'A', 'R7'),

		# A0
		('ORL', 'C', '/bit'),
		('AJMP', 'addr11'),
		('MOV', 'C', 'bit'),
		('INC', 'DPTR'),
		('MUL', 'AB'),
		('opcode A5 (reserved instruction)'),
		('MOV', '@R0', 'direct'),
		('MOV', '@R1', 'direct'),
		('MOV', 'R0', 'direct'),
		('MOV', 'R1', 'direct'),
		('MOV', 'R2', 'direct'),
		('MOV', 'R3', 'direct'),
		('MOV', 'R4', 'direct'),
		('MOV', 'R5', 'direct'),
		('MOV', 'R6', 'direct'),
		('MOV', 'R7', 'direct'),

		# B0
		('ANL', 'C', '/bit'),
		('ACALL', 'addr11'),
		('CPL', 'bit'),
		('CPL', 'C'),
		('CJNE', 'A', '#data', 'rel'),
		('CJNE', 'A', 'direct', 'rel'),
		('CJNE', '@R0', '#data', 'rel'),
		('CJNE', '@R1', '#data', 'rel'),
		('CJNE', 'R0', '#data', 'rel'),
		('CJNE', 'R1', '#data', 'rel'),
		('CJNE', 'R2', '#data', 'rel'),
		('CJNE', 'R3', '#data', 'rel'),
		('CJNE', 'R4', '#data', 'rel'),
		('CJNE', 'R5', '#data', 'rel'),
		('CJNE', 'R6', '#data', 'rel'),
		('CJNE', 'R7', '#data', 'rel'),

		# C0
		('PUSH', 'direct'),
		('AJMP', 'addr11'),
		('CLR', 'bit'),
		('CLR', 'C'),
		('SWAP', 'A'),
		('XCH', 'A', 'direct'),
		('XCH', 'A', '@R0'),
		('XCH', 'A', '@R1'),
		('XCH', 'A', 'R0'),
		('XCH', 'A', 'R1'),
		('XCH', 'A', 'R2'),
		('XCH', 'A', 'R3'),
		('XCH', 'A', 'R4'),
		('XCH', 'A', 'R5'),
		('XCH', 'A', 'R6'),
		('XCH', 'A', 'R7'),

		# D0
		('POP', 'direct'),
		('ACALL', 'addr11'),
		('SETB', 'bit'),
		('SETB', 'C'),
		('DA', 'A'),
		('DJNZ', 'direct', 'rel'),
		('XCHD', 'A', '@R0'),
		('XCHD', 'A', '@R1'),
		('DJNZ', 'R0', 'rel'),
		('DJNZ', 'R1', 'rel'),
		('DJNZ', 'R2', 'rel'),
		('DJNZ', 'R3', 'rel'),
		('DJNZ', 'R4', 'rel'),
		('DJNZ', 'R5', 'rel'),
		('DJNZ', 'R6', 'rel'),
		('DJNZ', 'R7', 'rel'),

		# E0
		('MOVX', 'A', '@DPTR'),
		('AJMP', 'addr11'),
		('MOVX', 'A', '@R0'),
		('MOVX', 'A', '@R1'),
		('CLR', 'A'),
		('MOV', 'A', 'direct'),
		('MOV', 'A', '@R0'),
		('MOV', 'A', '@R1'),
		('MOV', 'A', 'R0'),
		('MOV', 'A', 'R1'),
		('MOV', 'A', 'R2'),
		('MOV', 'A', 'R3'),
		('MOV', 'A', 'R4'),
		('MOV', 'A', 'R5'),
		('MOV', 'A', 'R6'),
		('MOV', 'A', 'R7'),

		# F0
		('MOVX', '@DPTR', 'A'),
		('ACALL', 'addr11'),
		('MOVX', '@R0', 'A'),
		('MOVX', '@R1', 'A'),
		('CPL', 'A'),
		('MOV', 'direct', 'A'),
		('MOV', '@R0', 'A'),
		('MOV', '@R1', 'A'),
		('MOV', 'R0', 'A'),
		('MOV', 'R1', 'A'),
		('MOV', 'R2', 'A'),
		('MOV', 'R3', 'A'),
		('MOV', 'R4', 'A'),
		('MOV', 'R5', 'A'),
		('MOV', 'R6', 'A'),
		('MOV', 'R7', 'A'),
	)
