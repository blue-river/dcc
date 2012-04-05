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

			#modified |= self.tryOptimizePushPopLocation()
			#modified |= self.tryOptimizePushPop()
			#modified |= self.tryOptimizePushDiscard()
			#modified |= self.tryOptimizeMov()
			#modified |= self.tryOptimizeCondSwap()
			#modified |= self.tryOptimizeCondJump()
			#modified |= self.tryOptimizeLjmp()
			#modified |= self.tryOptimizeTailCall()

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

	def tryOptimizePushDiscard(self):
		if not self.canGet(1):
			return False

		if not (self.get(0).type == 'PUSH direct' and self.get(1).type == 'DEC direct' and self.get(1).args[0] == 'SP'):
			return False

		self.remove(0, 1)
		return True

	pushBarriers = (
		'ACALL addr11',
		'CJNE A,direct,rel',
		'LCALL addr16',
		'POP direct',
		'PUSH direct',
		'comment',
		'label',
	)
	pushWindows = (
		'DEC direct',
		'MOV A,#data',
		'MOV A,Rn',
		'MOV DPTR,#data16',
		'MOV Rn,#data',
		'MOV Rn,direct',
		'MOV direct,#data',
		'MOV direct,Rn',
		'MOV direct,direct',
		'MOVX @DPTR,A',
		'MOVX A,@DPTR',
		'ORL A,Rn',
	)

	def tryOptimizePushPopLocation(self):
		# TODO also move pop up

		instruction = self.get(0)

		if not instruction.type in ('PUSH direct', 'POP direct'):
			return False

		push = instruction.type == 'PUSH direct'

		if push:
			otherInstruction = self.get(1)
		else:
			otherInstruction = self.get(-1)

		if otherInstruction.type in self.pushBarriers:
			return False

		if otherInstruction.type in self.pushWindows:
			mem = str(instruction.args[0])

			if otherInstruction.type == 'MOV A,#data':
				barrier = ['A']

			elif otherInstruction.type in ('MOV Rn,#data', 'DEC direct', 'MOV direct,#data'):
				barrier = [str(otherInstruction.args[0])]

			elif otherInstruction.type in ('MOV A,Rn', 'ORL A,Rn'):
				barrier = ['A', str(otherInstruction.args[0])]

			elif otherInstruction.type in ('MOV direct,Rn', 'MOV Rn,direct', 'MOV direct,direct'):
				barrier = [str(otherInstruction.args[0]), str(otherInstruction.args[1])]

			elif otherInstruction.type in ('MOVX A,@DPTR', 'MOVX @DPTR,A'):
				barrier = ['A', 'DPL', 'DPH']

			elif otherInstruction.type == 'MOV DPTR,#data16':
				barrier = []

			else:
				raise Exception("Internal error: unreachable for '%s'" % otherInstruction.type)

			if 'A' in barrier and 'ACC' not in barrier:
				barrier.append('ACC')
			elif 'ACC' in barrier and 'A' not in barrier:
				barrier.append('A')

			if mem in barrier or 'SP' in barrier:
				return False

			if push:
				self.remove(0,0)
				self.insert(1, instruction)
			else:
				self.remove(0,0)
				self.insert(-1, instruction)
			return True

		if self.options.debugOptimizer:
			print 'Possible push barrier ' + otherInstruction.type

		return False
		

	def tryOptimizePushPop(self):
		if not self.canGet(1):
			return False

		if not (self.get(0).type == 'PUSH direct' and self.get(1).type == 'POP direct'):
			return False

		source = self.get(0).args[0]
		target = self.get(1).args[0]

		self.remove(0,1)

		if source != target:
			self.insert(0, Asm('MOV direct,direct', target, source))
		
		return True

	def tryOptimizeTailCall(self):
		if not self.canGet(1):
			return False

		if not (self.get(0).type in ('LCALL addr16', 'ACALL addr11') and self.get(1).type == 'RET'):
			return False

		self.get(0).type = 'LJMP addr16'
		return True

	def tryOptimizeMov(self):
		'Assumption: R0-R7 = 0x00-0x07'

		if self.get(0).type == 'MOV direct,direct':
			# replace with shorter version
			target = self.get(0).args[0]
			source = self.get(0).args[1]

			if target < 8:
				self.remove(0, 0)
				self.insert(0, Asm('MOV Rn,direct', target, source))
				return True
			elif source < 8:
				self.remove(0, 0)
				self.insert(0, Asm('MOV direct,Rn', target, source))
				return True

		if self.get(0).type == 'MOV direct,Rn' and self.get(0).args[0] == 'ACC':
			# replace with shorter version
			source = self.get(0).args[1]

			self.remove(0, 0)
			self.insert(0, Asm('MOV A,Rn', source))
			return True

		if not self.canGet(1):
			return False

		if (self.get(0).type == 'MOV Rn,direct' and self.get(1).type == 'MOV Rn,direct') or \
			(self.get(0).type == 'MOV direct,direct' and self.get(1).type == 'MOV direct,direct'):
			# remove useless (x ->) y -> x
			if str(self.get(0).args[0]) == str(self.get(1).args[1]) and str(self.get(1).args[0]) == str(self.get(0).args[1]):
				self.remove(1,1)
				return True

		if self.get(0).type == 'MOV Rn,#data' and str(self.get(0).args[0]) == '0':
			# constants
			# assumption: R0 values are only used once

			if self.get(1).type == 'MOV A,Rn' and str(self.get(1).args[0]) == '0':
				self.get(1).type = 'MOV A,#data'
				self.get(1).args = (self.get(0).args[1],)
				self.remove(0, 0)
				return True

			if self.get(1).type == 'MOV direct,Rn' and str(self.get(1).args[1]) == '0':
				self.get(1).type = 'MOV direct,#data'
				self.get(1).args = (self.get(1).args[0], self.get(0).args[1])
				self.remove(0, 0)
				return True


			if self.get(1).type == 'PUSH direct' and self.canGet(2):
				if self.get(2).type == 'MOV Rn,direct':
					self.get(2).type = 'MOV Rn,#data'
					self.get(2).args = (self.get(2).args[0], self.get(0).args[1])
					self.remove(0, 0)
					return True


		if self.get(0).type == 'MOV Rn,#data' and self.get(1).type == 'MOV A,Rn' and self.get(2).type == 'POP direct':
			return False
			reg0 = self.get(0).args[0]
			reg1 = self.get(1).args[0]
			addr = self.get(2).args[0]

			if reg0 == reg1 == addr:
				data = self.get(0).args[1]
				
				self.remove(0, 1)
				self.insert(0, Asm('MOV A,#data', data))
				return True

		return False

	def tryOptimizeCondSwap(self):
		if not self.canGet(2):
			return False

		source = self.get(0)

		if source.type[0] != 'J':
			return False

		next = self.get(1)

		if next.type != 'SJMP rel':
			return False
		
		targetLabel = self.labels[source.args[-1]]

		if self.get(2) != targetLabel:
			return False

		# invert the jump condition
		if source.type[1] == 'N':
			source.type = 'J' + source.type[2:]
		else:
			source.type = 'JN' + source.type[1:]

		# swap the jump targets
		temp = source.args[-1]
		source.args[-1] = next.args[-1]
		next.args[-1] = temp

		return True

	def tryOptimizeCondJump(self):
		source = self.get(0)
		
		if source.type not in self.condJumps:
			return False

		sourceAddress = source.address + AsmSize[source.type]
		target = self.labels[source.args[-1]]
		
		if target.type != 'label':
			raise Exception("Internal error: expected label as target instruction but found '%s' instead" % target.type)

		jumpTarget = self.program[self.program.index(target) + 1]

		if jumpTarget.type not in ('AJMP rel', 'SJMP rel', 'LJMP rel'):
			return False

		finalTarget = self.labels[jumpTarget.args[0]]

		finalTargetAddress = finalTarget.address - AsmSize[jumpTarget.type]

		if self.isAddrInSJMPRange(sourceAddress, finalTargetAddress):
			source.args[-1] = jumpTarget.args[0]
			return True
		
		return False

	def tryOptimizeLjmp(self):
		source = self.get(0)

		if source.type not in ('ACALL addr11', 'AJMP addr11', 'LCALL addr16', 'LJMP addr16', 'SJMP rel'):
			return False

		targetLabel = self.labels[source.args[0]]

		if self.canGet(1):
			if source.type in ('AJMP addr11', 'LJMP addr16', 'SJMP rel'):
				# is the jump target the next instruction?
				if targetLabel is self.get(1):
					# remove the no-op jump
					self.remove(0, 0)
					return True

				targetInstruction = self.program[self.program.index(targetLabel) + 1]

				if source != targetInstruction:

					# is the jump target a jump instruction?
					if targetInstruction.type in ('AJMP addr11', 'LJMP addr16', 'SJMP rel'):
						# skip the intermediate jump
						source.type = 'LJMP addr16'
						source.args[0] = targetInstruction.args[0]
						return True

					# is the jump target a return instruction?
					if targetInstruction.type in ('RET', 'RETI'):
						# skip the intermediate jump
						source.type = targetInstruction.type
						source.args = ()
						return True

		oldType = source.type

		# try to use a shorter instruction if the target is within range
		# or when the target is out of range, revert to the longer instruction
		if source.type in ('LJMP addr16', 'SJMP rel', 'AJMP addr11'):
			if self.isInSJMPRange(source, targetLabel):
				source.type = 'SJMP rel'
			elif self.isInAJMPRange(source, targetLabel):
				source.type = 'AJMP addr11'
			else:
				source.type = 'LJMP addr16'

		elif source.type in ('LCALL addr16', 'ACALL addr11'):
			if self.isInAJMPRange(source, targetLabel):
				source.type = 'ACALL addr11'
			else:
				source.type = 'LCALL addr16'

		return source.type != oldType

	def isInSJMPRange(self, sourceInstruction, targetInstruction):
		'SJMP range: target address within -128..127 bytes of source address + 2'

		source = sourceInstruction.address + 2
		target = targetInstruction.address

		return self.isAddrInSJMPRange(source, target)

	def isAddrInSJMPRange(self, sourceAddress, targetAddress):
		return -128 <= targetAddress - sourceAddress <= 127

	def isInAJMPRange(self, sourceInstruction, targetInstruction):
		'AJMP range: target address within the same 2KB block of source address + 2'

		source = sourceInstruction.address + 2
		target = targetInstruction.address

		return target >> 11 == source >> 11

	# -----

	def canGet(self, offset):
		return self.pos + offset < len(self.program)

	def get(self, offset):
		return self.program[self.pos + offset]

	def remove(self, start, end):
		del self.program[self.pos + start:self.pos + end + 1]

	def insert(self, offset, *asm):
		self.program[self.pos + offset:self.pos + offset] = asm
