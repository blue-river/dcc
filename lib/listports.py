"""
Scan for serial ports.

Adapted from http://pyserial.svn.sourceforge.net/viewvc/pyserial/trunk/pyserial/examples/scan.py
"""

import serial
import glob

def scan():
	available = []
	for i in range(256):
		try:
			s = serial.Serial(i)
			available.append(s.portstr)
			s.close()   # explicit close 'cause of delayed GC in java
		except serial.SerialException:
			pass

	return available + glob.glob('/dev/cu.*') + glob.glob('/dev/ttyS*') + glob.glob('/dev/ttyUSB*')

def listPorts():
	ports = scan()
	if ports:
		print "Found ports:"
		for port in ports:
			print port
	else:
		print "No serial ports found."
