import ply.lex as lex

class HexTokenizer(object):
	
	def __init__(self):
		self.lexer = lex.lex(module=self)

	tokens = (
		'START',
		'HEX',
	)

	t_START = r':'
	t_HEX = r'[0-9A-Z][0-9A-Z]'
	
	t_ignore = '\r\n'

	def t_error(self, t):
		raise Exception("Unexpected character '%s'" % t.value[0])
