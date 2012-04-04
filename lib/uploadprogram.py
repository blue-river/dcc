import sys

from lib.hexreader import HexReader

class uploadProgram(object):

	def __init__(self, program, hardware):
		print 'Uploading program',

		self.hardware = hardware
		self.bufferStart = 0
		self.buffer = []
		self.lastAddress = -1

		hexreader = HexReader()
		hexreader.readHex(program, self.callback)
		self.writeBuffer()

		print
		print 'Program uploaded.'

	def writeBuffer(self):
		if not self.buffer:
			return

		self.hardware.writeCode(self.bufferStart, self.buffer)
		self.buffer = []
		sys.stdout.write('.')
		sys.stdout.flush()

	def callback(self, address, value):
		if address - 1 != self.lastAddress:
			self.writeBuffer()
			self.bufferStart = address

		if len(self.buffer) == 0xFF:
			self.writeBuffer()
			self.bufferStart = address

		self.lastAddress = address
		self.buffer.append(value)
