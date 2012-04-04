#!/usr/bin/python
from optparse import OptionParser
import os
import subprocess
import sys

usage = 'usage: %prog INPUT'
description = 'Assembles 8051 assembly instructions in INPUT to a .hex file.'

parser = OptionParser(usage=usage, description=description)
options, args = parser.parse_args()

if len(args) != 1:
	parser.error('1 argument expected, got %d' % len(args))

filename = args[0]

if filename[-4:] == '.asm':
	filename = filename[:-4]

if not os.path.exists(filename + '.asm'):
	parser.error("'%s.asm' is not a file." % filename)

process = subprocess.Popen(['as504.exe', '-l', filename + '.asm'], stdin=subprocess.PIPE)
# continue past the 'Press enter' prompt
process.communicate('\r\n')
process.wait()
if process.returncode != 0:
	sys.exit(1)

with open(filename + '.hex') as hexfile:
	hex = hexfile.read()

hex = hex.replace('\r\n', '\n')
with open(filename + '.hex', 'w') as hexfile:
	hexfile.write(hex)
