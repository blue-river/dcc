from asmgenerator import *
from pprint import pprint

class AsmOptimizer(object):
	'''
	The AsmOptimizer optimizes a given assembly program for size.
	In nearly all cases, a smaller program is faster than an equivalent
	larger program.
	'''

	#condJumps = ('JZ rel', 'JNZ rel', 'JC rel', 'JNC rel', 'JB bit,rel', 'JNB bit,rel', 'JBC bit,rel', 'CJNE A,direct,rel', 'CJNE A,#data,rel', 'CJNE Rn,#data,rel', 'CJNE @Ri,#data,rel', 'DJNZ Rn,rel', 'DJNZ direct,rel')
	#uncondJumps = ('AJMP addr11', 'LJMP addr16', 'SJMP rel')
	#jumps = condJumps + uncondJumps

	def __init__(self, program, options):
		self.program = program
		self.options = options

	def doPass(self):
		modified = False
		self.pos = 0

		self.determineInstructionLocations()
		self.locateLabels()
		self.mergeLabels()
		self.tryRemoveDeadLabels()

		modified |= self.tryEliminateDeadCode()

		while self.pos < len(self.program):
			self.tryRemoveComment()

			modified |= self.tryOptimizePushLocation()
			modified |= self.tryOptimizePushPop()
			modified |= self.tryOptimizePushDiscard()
			modified |= self.tryOptimizeDiscardPush()
			modified |= self.tryOptimizePeekPop()
			modified |= self.tryOptimizeSetPC()
			modified |= self.tryOptimizeTailCall()
			modified |= self.tryOptimizeNoop()

			self.pos += 1

		self.pos = 0

		return modified

	def determineInstructionLocations(self):
		'''
		Calculates the current address for each instruction.
		'''

		address = 0

		for instruction in self.program:
			instruction.address = address
			address += instruction.size()

	def locateLabels(self):
		self.labels = {}
		
		for instruction in self.program:
			if instruction.opcode == Label:
				if instruction.a.name in self.labels:
					raise Exception("Internal error: duplicate label '%s'" % instruction.args[0])

				self.labels[instruction.a.name] = instruction

	def mergeLabels(self):
		for label in self.labels:
			sourceLabel = self.labels[label].a.name
			index = self.program.index(self.labels[label])

			if self.program[index + 1].opcode != Label:
				continue

			while self.program[index + 1].opcode == Label:
				index += 1

			targetLabel = self.program[index].a.name

			for instruction in self.program:
				if isinstance(instruction.a, LabelReference) and instruction.a.name == sourceLabel:
					instruction.a.name = targetLabel
				if isinstance(instruction.b, LabelReference) and instruction.b.name == sourceLabel:
					instruction.b.name = targetLabel

	def tryRemoveDeadLabels(self):
		for label in self.labels:
			self.labels[label].targeted = False

		for instruction in self.program:
			if instruction.opcode in (Label, ):
				continue
			elif instruction.opcode == JSR:
				self.labels[instruction.a.name].targeted = True
			elif isinstance(instruction.b, LabelReference) and instruction.b.name in self.labels:
				self.labels[instruction.b.name].targeted = True

		for label in self.labels:
			if not self.labels[label].targeted:
				index = self.program.index(self.labels[label])
				self.remove(index, index)

	def tryEliminateDeadCode(self):
		locationsToVisit = [0]

		for instruction in self.program:
			instruction.reachable = False

		while locationsToVisit:
			location = locationsToVisit.pop()

			instruction = self.program[location]
			if instruction.reachable:
				continue

			instruction.reachable = True

			# quick hack
			if instruction.opcode in (IFE, IFN, IFG, IFB):
				locationsToVisit.append(location + 2)
			elif instruction.opcode in (JSR,):
				locationsToVisit.append(self.program.index(self.labels[instruction.a.name]))
			elif isinstance(instruction.a, PC):
				if instruction.opcode != SET:
					raise Exception("Internal error: optimizer bailing out on unpredictable jump opcode")
				if isinstance(instruction.b, Pop):
					continue
				if not isinstance(instruction.b, LabelReference):
					print instruction.asm()
					raise Exception("Internal error: optimizer bailing out on unpredictable jump target")

				locationsToVisit.append(self.program.index(self.labels[instruction.b.name]))
				continue

			locationsToVisit.append(location + 1)

		location = 0

		modified = False

		while location < len(self.program):
			if self.program[location].reachable:
				location += 1
			else:
				del self.program[location]
				modified = True

		return modified

	def tryRemoveComment(self):
		if self.get(0).opcode == Comment:
			self.remove(0, 0)

	def tryOptimizePushLocation(self):
		if not (self.canGet(1)):
			return False

		push = self.get(0)
		other = self.get(1)

		if not (push.opcode == SET and isinstance(push.a, Push) and isinstance(push.b, Literal)):
			return False

		if other.opcode in (JSR, Label) or isinstance(other.a, (Push, Peek, Pop, PC, SP)) or isinstance(other.b, (Pop, Peek, Push, PC, SP)):
			return False

		if not(isinstance(push.b, Literal)) and push.b.asm() == other.a.asm():
			return False

		self.remove(0, 0)
		self.insert(1, push)
		return True

	def tryOptimizePushDiscard(self):
		if not self.canGet(1):
			return False

		if not (self.get(1).opcode == ADD and isinstance(self.get(1).a, SP) and isinstance(self.get(1).b, Literal) and self.get(1).b.value >= 1):
			return False

		if not (self.get(0).opcode in (SET, MOD, AND, BOR, XOR) and isinstance(self.get(0).a, Push) and not isinstance(self.get(0).b, (Push, Pop))):
				return False

		self.get(1).b.value -= 1
		self.remove(0, 0)
		return True

	def tryOptimizeDiscardPush(self):
		if not self.canGet(1):
			return False

		discard = self.get(0)

		if not (discard.opcode == ADD and isinstance(discard.a, SP) and isinstance(discard.b, Literal) and discard.b.value == 1):
			return False

		push = self.get(1)

		if not (push.opcode == SET and isinstance(push.a, Push)):
			return False

		self.remove(0, 0)
		push.a = Peek()
		return True

	def tryOptimizePeekPop(self):
		if not self.canGet(1):
			return False

		peek = self.get(0)
		pop = self.get(1)

		if not (peek.opcode in (SET, ADD, SUB, MUL, DIV, MOD, SHL, SHR, AND, BOR, XOR) and isinstance(peek.a, Peek)):
			return False

		if not (pop.opcode == SET and isinstance(pop.b, Pop)) or isinstance(pop.a, (Peek, Push)):
			return False

		if not (peek.b.asm() == pop.a.asm()):
			return False

		pop.opcode = peek.opcode
		self.remove(0, 0)
		return True

	def tryOptimizePushPop(self):
		if not self.canGet(1):
			return False

		if not (self.get(0).opcode == SET and isinstance(self.get(0).a, Push)):
			return False
		if isinstance(self.get(0).b, (Push, Peek, Pop)):
			return False
		if not isinstance(self.get(1).b, Pop):
			return False

		source = self.get(0)
		target = self.get(1)

		self.remove(0,1)

		if source.b.asm() != target.a.asm():
			self.insert(0, Instruction(target.opcode, target.a, source.b))
		
		return True

	def tryOptimizeTailCall(self):
		if not self.canGet(1):
			return False

		if not (self.get(0).opcode == JSR and self.get(1).opcode == SET and isinstance(self.get(1).a, PC) and isinstance(self.get(1).b, Pop)):
			return False

		instr = self.get(0)

		instr.opcode = SET
		instr.b = instr.a
		instr.a = PC()
		return True

	def tryOptimizeSetPC(self):
		if not self.canGet(1):
			return False

		source = self.get(0)
		target = self.get(1)

		if not (target.opcode == Label and source.opcode == SET and isinstance(source.a, PC)):
			return False
		if not (isinstance(source.b, LabelReference) and source.b.name == target.a.name):
			return False

		self.remove(0, 0)

		return True

	def tryOptimizeNoop(self):
		target = self.get(0)

		if (target.opcode in (ADD, SUB, SHL, SHR, BOR, XOR) and isinstance(target.b, Literal) and target.b.value == 0):
			self.remove(0, 0)
			return True

		if (target.opcode in (MUL, DIV) and isinstance(target.b, Literal) and target.b.value == 1):
			self.remove(0, 0)
			return True

		return False

	# -----

	def canGet(self, offset):
		return self.pos + offset < len(self.program)

	def get(self, offset):
		return self.program[self.pos + offset]

	def remove(self, start, end):
		del self.program[self.pos + start:self.pos + end + 1]

	def insert(self, offset, *asm):
		self.program[self.pos + offset:self.pos + offset] = asm
