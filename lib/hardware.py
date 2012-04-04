from serial import Serial

class Hardware(object):

	def __init__(self, port, debug=False):
		self.debug = debug

		self.port = Serial(port, timeout=0.01)

		self.resetConnection()

	def resetConnection(self):
		print 'Establishing connection...'

		repeatCount = 0

		while True:
			if repeatCount == 100:
				print 'Mon51 does not respond. Please reset the board to continue.'

			repeatCount += 1
			self.send([0x11])
			if self.read(wait=False) != [0xff]:
				continue

			self.send([0x11])
			if self.read(wait=False) != [0x00]:
				continue

			self.sendWithChecksum([0x10, 0x02])
			if self.read() != [0x06, 0x00, ord('V'), ord('3'), ord('.'), ord('0'), 0x04]:
				raise Exception('Unknown handshake')

			print 'Connection established.'

			return

	def step(self):
		self.sendWithChecksum([0x0C])
		self.read()

	def run(self):
		self.sendWithChecksum([0x08, 0x00, 0x01, 0x05, 0x00, 0x00, 0x05, 0xff, 0xff])
		self.read()

	def stop(self):
		self.send([0x1B])
		
		self.resetConnection()

	def getPC(self):
		inbytes = self.readMemory(0x00, 0x00, 0x00)

		return inbytes[0] << 8 | inbytes[1]

	def setPC(self, address):
		self.writeMemory(0x00, 0x00, [address >> 8, address & 0xff])

		# HACK to work around strange response
		self.resetConnection()

	def getRegisters(self):
		self.sendWithChecksum([0x08, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
		return self.readMemoryResponse()

	def writeCode(self, address, bytes):
		self.writeMemory(0x05, address, bytes)

	def readCode(self, address, length):
		return self.readMemory(0x05, address, length)

	def writeDirect(self, address, bytes):
		self.writeMemory(0x04, address, bytes)

	def readDirect(self, address, length):
		return self.readMemory(0x04, address, length)

	def writeIndirect(self, address, bytes):
		self.writeMemory(0x01, address, bytes)

	def readIndirect(self, address, length):
		return self.readMemory(0x01, address, length)

	def writeExternal(self, address, bytes):
		self.writeMemory(0x02, address, bytes)

	def readExternal(self, address, length):
		return self.readMemory(0x02, address, length)

	def writeMemory(self, type, address, bytes):
		self.sendWithChecksum([0x02, type, address >> 8, address & 0xff, len(bytes)] + bytes)
		self.read()

	def readMemory(self, type, address, length):
		self.sendWithChecksum([0x04, type, address >> 8, address & 0xff, length])
		return self.readMemoryResponse()

	def readMemoryResponse(self):
		inbytes = self.readWithChecksum()

		if inbytes[0] != 0x02:
			raise Exception('Invalid response')

		del inbytes[0]

		return inbytes

	def read(self, wait=True):
		inbytes = []

		while len(inbytes) < 512:
			data = self.port.read(256)

			if not data and (inbytes or not wait):
				if self.debug:
					print 'IN:  ' + ' '.join('%02X' % byte for byte in inbytes)
					print '%02X   %s' % (len(inbytes), repr(''.join(chr(byte) for byte in inbytes)))
					print
				return inbytes

			inbytes += (ord(byte) for byte in data)

		raise Exception('Huge response, driver bug?')

	def readWithChecksum(self):
		inbytes = self.read()

		if sum(inbytes) % 0x100 != 0:
			raise Exception('Invalid checksum received')

		inbytes.pop()

		return inbytes

	def send(self, data):
		if self.debug:
			print 'OUT: ' + ' '.join('%02X' % byte for byte in data)
			print '     ' + repr(''.join(chr(byte) for byte in data))
			print
		self.port.write(''.join(chr(byte) for byte in data))

	def sendWithChecksum(self, data):
		sum = 0
		for byte in data:
			sum += byte

		checksum = (0x100 - sum) % 0x100
		self.send(data + [checksum])

	def reset(self):
		self.setPC(0x0000)
