from hextokenizer import HexTokenizer

class HexReader(object):

	def __init__(self):
		self.tokenizer = HexTokenizer()

	def readHex(self, hexStr, callback):
		self.tokenizer.lexer.input(hexStr)

		while True:
			token = self.readToken()

			if not token:
				break

			if token.type != 'START':
				raise Exception("Invalid input: found '%s' but expected ':'" % token.value)

			self.sum = 0

			length = int(self.readToken().value, 16)
			address = int(self.readToken().value, 16) << 8 | int(self.readToken().value, 16)

			type = int(self.readToken().value, 16)

			if type == 0:
				while length != 0:
					value = int(self.readToken().value, 16)

					callback(address, value)

					address += 1
					length -= 1

				checksum = (0x100 - self.sum) % 0x100
				readChecksum = int(self.readToken().value, 16)
				if checksum != readChecksum:
					raise Exception('Invalid input: expected checksum 0x%X but got 0x%X' % (checksum, readChecksum))

			elif type == 1:
				# ignore, end			
				self.readToken()

			else:
				raise Exception('Unknown type: %X' % type)

	def readToken(self):
		token = self.tokenizer.lexer.token()

		if token and token.type == 'HEX':
			value = int(token.value, 16)
			self.sum += value

		return token
