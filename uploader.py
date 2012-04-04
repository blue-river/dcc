#!/usr/bin/python

from optparse import OptionParser

from lib.hardware import Hardware
from lib.listports import listPorts
from lib.uploadprogram import uploadProgram

def main():
	usage = 'usage: %prog SERIALPORT HEXFILE'
	description = 'Uploads HEXFILE to the device connected to SERIALPORT, and runs the program.'

	parser = OptionParser(usage=usage, description=description)
	parser.add_option('--list-ports', action='store_true', dest='listPorts', help='Lists the serial ports available on this system and exits', default=False)

	options, args = parser.parse_args()

	if options.listPorts:
		listPorts()
		return

	if len(args) == 0:
		parser.print_help()
		return

	if len(args) != 2:
		parser.error('2 arguments expected, got %d' % len(args))

	hardware = Hardware(args[0])

	with open(args[1]) as inputFile:
		prog = inputFile.read()	

	uploadProgram(prog, hardware)

	hardware.run()

	print 'Program started.'

if __name__ == '__main__':
	main()
