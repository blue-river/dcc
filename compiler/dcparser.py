import os

import ply.yacc as yacc

from compilererror import CompilerError
from dctokenizer import DCTokenizer
from syntaxitems import *

class DCParser(object):

	def __init__(self, options):
		self.tokenizer = DCTokenizer()
		self.tokens = self.tokenizer.tokens
		self.parser = yacc.yacc(module=self, debug=options.debugParser, tabmodule='compiler.dcparsetab', outputdir=os.path.dirname(os.path.realpath(__file__)))

		self.foundModuleReferences = set()

	precedence = (
		('left', 'OR'),
		('left', 'XOR'),
		('left', 'AMPERSAND'),
		('left', 'BOOLEANOR'),
		('left', 'BOOLEANAND'),
		('left', 'EQUALS', 'NOTEQUALS'),
		('left', 'PLUS', 'MINUS'),
		('left', 'ASTERISK', 'SLASH'),
		('right', 'NOT', 'BOOLEANNOT'),
	)

# structure

	def p_module(self, p):
		'module : datafieldsorfunctions'
		p[0] = Module(self.filename, p.lineno(1), self.modulename, p[1].datafields, p[1].functions)

	def p_datafieldlist(self, p):
		'datafieldsorfunctions : datafield datafieldsorfunctions'
		d = p[2]
		d.datafields.append(p[1])
		p[0] = d

	def p_functionlist(self, p):
		'datafieldsorfunctions : function datafieldsorfunctions'
		d = p[2]
		d.functions.append(p[1])
		p[0] = d

	def p_nomodulecontents(self, p):
		'datafieldsorfunctions :'
		d = AbstractSyntaxItem(self.filename, p.lineno(0))
		d.datafields = []
		d.functions = []
		p[0] = d

	def p_datafieldwithdefault(self, p):
		'datafield : DATATYPE unqualifiedidentifier ASSIGN integer SEMICOLON'
		d = DataField(self.filename, p.lineno(1), p[1], p[2])
		d.default = p[4]
		p[0] = d

	def p_datafield(self, p):
		'datafield : DATATYPE unqualifiedidentifier SEMICOLON'
		d = DataField(self.filename, p.lineno(1), p[1], p[2])
		p[0] = d

	def p_addr(self, p):
		'datafield : ADDR DATATYPE unqualifiedidentifier ASSIGN integer SEMICOLON'
		d = DataField(self.filename, p.lineno(1), p[2], p[3])
		# TODO check range
		d.address = p[5]
		p[0] = d

	def p_const(self, p):
		'datafield : CONST DATATYPE unqualifiedidentifier ASSIGN integer SEMICOLON'
		p[0] = ConstantDataField(self.filename, p.lineno(1), p[2], p[3], p[5])

	def p_function(self, p):
		'function : DATATYPE unqualifiedidentifier LEFTPAREN functionargs RIGHTPAREN LEFTBRACE functionlocals statementblock RIGHTBRACE'
		if self.modulename == 'main' and p[2] == 'main':
			f = MainFunction
		else:
			f = Function

		p[0] = f(self.filename, p.lineno(1), p[1], p[2], p[4], p[7], p[8])

	def p_functionargs(self, p):
		'functionargs : DATATYPE unqualifiedidentifier COMMA functionargs'
		arg = LocalVariable(self.filename, p.lineno(1), p[1], p[2]);
		p[0] = [arg] + p[4]

	def p_functionargsone(self, p):
		'functionargs : DATATYPE unqualifiedidentifier'
		arg = LocalVariable(self.filename, p.lineno(1), p[1], p[2])
		p[0] = [arg]

	def p_nofunctionargs(self, p):
		'functionargs :'
		p[0] = []

	def p_functionlocals(self, p):
		'functionlocals : DATATYPE unqualifiedidentifier SEMICOLON functionlocals'
		local = LocalVariable(self.filename, p.lineno(1), p[1], p[2])
		p[0] = [local] + p[4]

	def p_nofunctionlocals(self, p):
		'functionlocals :'
		p[0] = []

# integers

	def p_integer(self, p):
		'''integer : DECIMAL
		           | HEXADECIMAL
				   | BINARY'''
		p[0] = p[1]

# identifiers

	def p_qualifiedidentifier(self, p):
		'qualifiedidentifier : IDENTIFIER DOT IDENTIFIER'
		p[0] = p[1] + '.' + p[3]
		self.foundModuleReferences.add(p[1])

	def p_unqualifiedidentifier(self, p):
		'unqualifiedidentifier : IDENTIFIER'
		p[0] = p[1]

	def p_anyidentifier(self, p):
		'''identifier : unqualifiedidentifier
		              | qualifiedidentifier'''
		p[0] = p[1]

# statements

	def p_statementblockfinal(self, p):
		'statementblock : statementblockcontents'
		p[0] = StatementBlock(self.filename, p.lineno(1), p[1])

	def p_statementblock(self, p):
		'statementblockcontents : statement statementblockcontents'
		p[0] = [p[1]] + p[2]

	def p_emptystatementblock(self, p):
		'statementblockcontents :'
		p[0] = []

	def p_expressionstatement(self, p):
		'statement : expression SEMICOLON'
		p[0] = Discard(self.filename, p.lineno(1), p[1])

# control flow

	def p_ifstatement(self, p):
		'statement : if'
		p[0] = p[1]

	def p_if(self, p):
		'if : IF LEFTPAREN booleanexpression RIGHTPAREN LEFTBRACE statementblock RIGHTBRACE'
		p[0] = If(self.filename, p.lineno(1), p[3], p[6], StatementBlock(self.filename, p.lineno(7), []))

	def p_ifelse(self, p):
		'if : IF LEFTPAREN booleanexpression RIGHTPAREN LEFTBRACE statementblock RIGHTBRACE ELSE LEFTBRACE statementblock RIGHTBRACE'
		p[0] = If(self.filename, p.lineno(1), p[3], p[6], p[10])

	def p_ifelseif(self, p):
		'if : IF LEFTPAREN booleanexpression RIGHTPAREN LEFTBRACE statementblock RIGHTBRACE ELSE if'
		p[0] = If(self.filename, p.lineno(1), p[3], p[6], StatementBlock(self.filename, p.lineno(9), [p[9]]))

	def p_loop(self, p):
		'statement : LOOP LEFTBRACE statementblock RIGHTBRACE'
		p[0] = Loop(self.filename, p.lineno(1), p[3])

	def p_break(self, p):
		'statement : BREAK SEMICOLON'
		p[0] = Break(self.filename, p.lineno(1))

	def p_continue(self, p):
		'statement : CONTINUE SEMICOLON'
		p[0] = Continue(self.filename, p.lineno(1))

	def p_repeat(self, p):
		'statement : REPEAT LEFTPAREN expression RIGHTPAREN LEFTBRACE statementblock RIGHTBRACE'
		p[0] = Repeat(self.filename, p.lineno(1), p[3], p[6])

	def p_while(self, p):
		'statement : WHILE LEFTPAREN booleanexpression RIGHTPAREN LEFTBRACE statementblock RIGHTBRACE'
		p[0] = While(self.filename, p.lineno(1), p[3], p[6])

# expressions

	def p_identifier(self, p):
		'expression : identifier'
		p[0] = Identifier(self.filename, p.lineno(1), p[1])

	def p_constant(self, p):
		'expression : integer'
		p[0] = Constant(self.filename, p.lineno(1), int(p[1]))

	def p_parentheses(self, p):
		'expression : LEFTPAREN expression RIGHTPAREN'
		p[0] = p[2]

	def p_dereference(self, p):
		'expression : ASTERISK expression'
		p[0] = Dereference(self.filename, p.lineno(1), p[2])

	def p_addressof(self, p):
		'expression : AMPERSAND identifier'
		p[0] = AddressOf(self.filename, p.lineno(1), p[2])

# boolean expressions

	def p_booleanconstant(self, p):
		'''booleanexpression : TRUE
		                     | FALSE'''
		p[0] = BooleanConstant(self.filename, p.lineno(1), p[1] == 'true')

	def p_getbit(self, p):
		'booleanexpression : expression BITOPERATOR integer'
		p[0] = GetBit(self.filename, p.lineno(2), p[1], p[3])

	def p_equals(self, p):
		'booleanexpression : expression EQUALS expression'
		p[0] = Equals(self.filename, p.lineno(2), p[1], p[3])

	def p_notequals(self, p):
		'booleanexpression : expression NOTEQUALS expression'
		p[0] = NotEquals(self.filename, p.lineno(2), p[1], p[3])

	def p_greaterthan(self, p):
		'booleanexpression : expression GREATERTHAN expression'
		p[0] = GreaterThan(self.filename, p.lineno(2), p[1], p[3])

	def p_greaterequals(self, p):
		'booleanexpression : expression GREATEREQUALS expression'
		p[0] = GreaterEquals(self.filename, p.lineno(2), p[1], p[3])

	def p_lessthan(self, p):
		'booleanexpression : expression LESSTHAN expression'
		p[0] = LessThan(self.filename, p.lineno(2), p[1], p[3])

	def p_lessequals(self, p):
		'booleanexpression : expression LESSEQUALS expression'
		p[0] = LessEquals(self.filename, p.lineno(2), p[1], p[3])

	def p_booleannot(self, p):
		'booleanexpression : BOOLEANNOT booleanexpression'
		p[0] = BooleanNot(self.filename, p.lineno(1), p[2])

	def p_booleanand(self, p):
		'booleanexpression : booleanexpression BOOLEANAND booleanexpression'
		p[0] = BooleanAnd(self.filename, p.lineno(2), p[1], p[3])

	def p_booleanor(self, p):
		'booleanexpression : booleanexpression BOOLEANOR booleanexpression'
		p[0] = BooleanOr(self.filename, p.lineno(2), p[1], p[3])

	def p_booleanequals(self, p):
		'booleanexpression : booleanexpression EQUALS booleanexpression'
		p[0] = BooleanEquals(self.filename, p.lineno(2), p[1], p[3])

	def p_booleannotequals(self, p):
		'booleanexpression : booleanexpression NOTEQUALS booleanexpression'
		p[0] = BooleanNotEquals(self.filename, p.lineno(2), p[1], p[3])

	def p_booleanparentheses(self, p):
		'booleanexpression : LEFTPAREN booleanexpression RIGHTPAREN'
		p[0] = p[2]

# operators

	def p_binaryoperatorplus(self, p):
		'expression : expression PLUS expression'
		p[0] = Addition(self.filename, p.lineno(2), p[1], p[3])

	def p_binaryoperatorminus(self, p):
		'expression : expression MINUS expression'
		p[0] = Subtraction(self.filename, p.lineno(2), p[1], p[3])

	def p_binaryoperatortimes(self, p):
		'expression : expression ASTERISK expression'
		p[0] = Multiplication(self.filename, p.lineno(2), p[1], p[3])

	def p_binaryoperatordivision(self, p):
		'expression : expression SLASH expression'
		p[0] = Division(self.filename, p.lineno(2), p[1], p[3])

	def p_binaryoperatorand(self, p):
		'expression : expression AMPERSAND expression'
		p[0] = And(self.filename, p.lineno(2), p[1], p[3])

	def p_binaryoperatoror(self, p):
		'expression : expression OR expression'
		p[0] = Or(self.filename, p.lineno(2), p[1], p[3])

	def p_binaryoperatorxor(self, p):
		'expression : expression XOR expression'
		p[0] = Xor(self.filename, p.lineno(2), p[1], p[3])

	def p_binaryoperatorshiftleft(self, p):
		'expression : expression SHIFTLEFT expression'
		p[0] = ShiftLeft(self.filename, p.lineno(2), p[1], p[3])

	def p_binaryoperatorshiftright(self, p):
		'expression : expression SHIFTRIGHT expression'
		p[0] = ShiftRight(self.filename, p.lineno(2), p[1], p[3])

	def p_unaryoperatornot(self, p):
		'expression : NOT expression'
		p[0] = Not(self.filename, p.lineno(1), p[2])

# assignment

	def p_assignment(self, p):
		'statement : identifier ASSIGN expression SEMICOLON'
		p[0] = Assignment(self.filename, p.lineno(2), p[1], p[3])

	def p_setbit(self, p):
		'statement : identifier BITOPERATOR integer ASSIGN booleanexpression SEMICOLON'
		p[0] = SetBit(self.filename, p.lineno(4), p[1], p[3], p[5])

	def p_addassign(self, p):
		'statement : identifier PLUSASSIGN expression SEMICOLON'
		i = Identifier(self.filename, p.lineno(1), p[1])
		expr = p[3]
		op = Addition(self.filename, p.lineno(2), i, expr)
		p[0] = Assignment(self.filename, p.lineno(2), p[1], op)

	def p_subtractassign(self, p):
		'statement : identifier MINUSASSIGN expression SEMICOLON'
		i = Identifier(self.filename, p.lineno(1), p[1])
		expr = p[3]
		op = Subtraction(self.filename, p.lineno(2), i, expr)
		p[0] = Assignment(self.filename, p.lineno(2), p[1], op)

	def p_multiplyassign(self, p):
		'statement : identifier ASTERISKASSIGN expression SEMICOLON'
		i = Identifier(self.filename, p.lineno(1), p[1])
		expr = p[3]
		op = Multiplication(self.filename, p.lineno(2), i, expr)
		p[0] = Assignment(self.filename, p.lineno(2), p[1], op)

	def p_divideassign(self, p):
		'statement : identifier SLASHASSIGN expression SEMICOLON'
		i = Identifier(self.filename, p.lineno(1), p[1])
		expr = p[3]
		op = Division(self.filename, p.lineno(2), i, expr)
		p[0] = Assignment(self.filename, p.lineno(2), p[1], op)

	def p_orassign(self, p):
		'statement : identifier ORASSIGN expression SEMICOLON'
		i = Identifier(self.filename, p.lineno(1), p[1])
		expr = p[3]
		op = Or(self.filename, p.lineno(2), i, expr)
		p[0] = Assignment(self.filename, p.lineno(2), p[1], op)

	def p_plusassign(self, p):
		'statement : identifier ANDASSIGN expression SEMICOLON'
		i = Identifier(self.filename, p.lineno(1), p[1])
		expr = p[3]
		op = And(self.filename, p.lineno(2), i, expr)
		p[0] = Assignment(self.filename, p.lineno(2), p[1], op)

	def p_increment(self, p):
		'statement : identifier INCREMENT SEMICOLON'
		p[0] = Increment(self.filename, p.lineno(2), p[1])

	def p_decrement(self, p):
		'statement : identifier DECREMENT SEMICOLON'
		p[0] = Decrement(self.filename, p.lineno(2), p[1])

# dereferenced assignment

	def p_derefassignment(self, p):
		'statement : ASTERISK expression ASSIGN expression SEMICOLON'
		p[0] = DerefAssignment(self.filename, p.lineno(3), p[2], p[4])

# call, return

	def p_call(self, p):
		'expression : identifier LEFTPAREN callargs RIGHTPAREN'
		p[0] = Call(self.filename, p.lineno(2), p[1], p[3])

	def p_callargs(self, p):
		'callargs : expression COMMA callargs'
		p[0] = [p[1]] + p[3]

	def p_callargsone(self, p):
		'callargs : expression'
		p[0] = [p[1]]

	def p_nocallargs(self, p):
		'callargs :'
		p[0] = []

	def p_return(self, p):
		'statement : RETURN expression SEMICOLON'
		p[0] = ReturnValue(self.filename, p.lineno(1), p[2])

	def p_returnnothing(self, p):
		'statement : RETURN SEMICOLON'
		p[0] = Return(self.filename, p.lineno(1))

# --

	def p_error(self, p):
		raise CompilerError(self.filename, p.lineno, 'Unexpected %s \'%s\'' % (p.type.lower(), p.value))


	def parse(self, filename, modulename, input):
		self.filename = filename
		self.modulename = modulename
		self.tokenizer.filename = filename

		parsetree = self.parser.parse(input, lexer=self.tokenizer.lexer, tracking=True)
		return parsetree, self.foundModuleReferences
