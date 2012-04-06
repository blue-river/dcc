import ply.lex as lex

from compilererror import CompilerError

class DCTokenizer(object):

	def __init__(self):
		self.lexer = lex.lex(module=self)

	reserved = {
		'addr': 'ADDR',
		'break': 'BREAK',
		'int': 'DATATYPE',
		'const': 'CONST',
		'continue': 'CONTINUE',
		'else': 'ELSE',
		'false': 'FALSE',
		'if': 'IF',
		'loop': 'LOOP',
		'repeat': 'REPEAT',
		'return': 'RETURN',
		'true': 'TRUE',
		'void': 'DATATYPE',
		'while': 'WHILE',
	}

	tokens = (
		'AMPERSAND',
		'ANDASSIGN',
		'ASSIGN',
		'ASTERISK',
		'ASTERISKASSIGN',
		'BINARY',
		'BITOPERATOR',
		'BOOLEANAND',
		'BOOLEANNOT',
		'BOOLEANOR',
		'COMMA',
		'DECIMAL',
		'DECREMENT',
		'DOT',
		'EQUALS',
		'GREATEREQUALS',
		'GREATERTHAN',
		'HEXADECIMAL',
		'IDENTIFIER',
		'INCREMENT',
		'LEFTBRACE',
		'LEFTPAREN',
		'LESSEQUALS',
		'LESSTHAN',
		'MINUS',
		'MINUSASSIGN',
		'NOT',
		'NOTEQUALS',
		'OR',
		'ORASSIGN',
		'PLUS',
		'PLUSASSIGN',
		'RIGHTBRACE',
		'RIGHTPAREN',
		'SEMICOLON',
		'SLASH',
		'XOR',
	) + tuple(set(reserved.values()))

	# assignment operators
	t_ANDASSIGN = r'&='
	t_ASSIGN = r'='
	t_ASTERISKASSIGN = r'\*='
	t_DECREMENT = r'--'
	t_INCREMENT = r'\+\+'
	t_MINUSASSIGN = r'-='
	t_ORASSIGN = r'\|='
	t_PLUSASSIGN = r'\+='

	# operators
	t_AMPERSAND = r'&'
	t_ASTERISK = r'\*'
	t_BITOPERATOR = r'@'
	t_BOOLEANAND = r'&&'
	t_BOOLEANNOT = r'!'
	t_BOOLEANOR = r'\|\|'
	t_EQUALS = r'=='
	t_GREATEREQUALS = r'>='
	t_GREATERTHAN = r'>'
	t_LESSEQUALS = r'<='
	t_LESSTHAN = r'<'
	t_MINUS = r'-'
	t_NOT = r'~'
	t_NOTEQUALS = r'!='
	t_OR = r'\|'
	t_PLUS = r'\+'
	t_SLASH = r'/'
	t_XOR = r'\^'

	# delimiters
	t_COMMA = r','
	t_DOT = r'\.'
	t_LEFTBRACE = r'{'
	t_LEFTPAREN = r'\('
	t_RIGHTBRACE = r'}'
	t_RIGHTPAREN = r'\)'
	t_SEMICOLON = r';'

	def t_IDENTIFIER(self, t):
		r'[a-zA-Z_][a-zA-Z0-9_]*'
		t.type = self.reserved.get(t.value, 'IDENTIFIER')
		return t

	def t_BINARY(self, t):
		r'0b[01]+'
		t.value = int(t.value, 2)
		return t

	def t_HEXADECIMAL(self, t):
		r'0x[0-9A-Fa-f]+'
		t.value = int(t.value, 16)
		return t

	def t_DECIMAL(self, t):
		r'\d+'
		t.value = int(t.value)
		return t

	def t_newline(self, t):
		r'\n+'
		t.lexer.lineno += len(t.value)

	def t_comment(self, t):
		r'//.*'

	t_ignore = ' \t\r';

	def t_error(self, t):
		raise CompilerError(self.filename, t.lineno, "Unexpected character '%s'" % t.value[0])
