#!/usr/bin/env VERSIONER_PYTHON_PREFER_32_BIT=yes python

from optparse import OptionParser

from debugger import cli
from lib.hardware import Hardware
from lib.listports import listPorts

def main():
	usage = 'usage: %prog SERIALPORT'
	description = 'Starts the debugger for the device connected to SERIALPORT.'

	parser = OptionParser(usage=usage, description=description)
	parser.add_option('--list-ports', action='store_true', dest='listPorts', help='Lists the serial ports available on this system and exits', default=False)

	options, args = parser.parse_args()

	if options.listPorts:
		listPorts()
		return

	if len(args) == 0:
		parser.print_help()
		return

	if len(args) != 1:
		parser.error('1 argument expected, got %d' % len(args))
	
	cli.run(Hardware(args[0]))


if __name__ == '__main__':
	main()
