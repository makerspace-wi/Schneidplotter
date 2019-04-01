#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
from hpgl import HPGL
try:
	import serial
except:
	print("You need to install pyserial. "
		"On Debian/Ubuntu try "
		"sudo apt-get install python-serial")
	exit(1)

# make input python2 and python3 compatible
try:
	input = raw_input
except NameError:
	pass

parser = argparse.ArgumentParser(description="Process all arguments ")
parser.add_argument("-p", "--port", metavar="PORT", type=str, help="Serial port (default: /dev/ttyUSB0)", default="/dev/ttyUSB0")
parser.add_argument("-m", "--magic", action="store_true", help="Enable auto-optimize")
parser.add_argument("-w", "--width", metavar="WIDTH", type=int, help="Scale to width in mm")
parser.add_argument("-v", "--preview", action="store_true", help="Show preview window before plotting")
parser.add_argument("--mirror", action="store_true", help="Mirror on X-axis for inverted cuts (T-Shirts etc.)")
parser.add_argument("--pen", action="store_true", help="Disable cut optimization for rotating knifes")
parser.add_argument("file", type=str, help="the HPGL-file you want to plot")
args = parser.parse_args()

try:
	HPGLinput = HPGL(args.file)
except:
	print("no/wrong/empty file given in argument.")
	print("")
	raise


# do optimize stuff:
blade_optimize = False
optimize = False
reroute = False
rotate180 = False
mirror = False
margin = 5

if args.mirror:
	mirror = True

if args.magic:
	blade_optimize = True
	reroute = True
	optimize = True
	rotate180 = True

if args.width is not None:
	HPGLinput.scaleToWidth(args.width)

if args.pen:
	blade_optimize = False

if rotate180:
	HPGLinput.mirrorX()
	HPGLinput.mirrorY()

if mirror:
	HPGLinput.mirrorX()

if optimize:
	HPGLinput.optimize()
	HPGLinput.fit()

if blade_optimize:
	HPGLinput.optimizeCut(0.25)
	HPGLinput.bladeOffset(0.25)

if reroute:
	HPGLinput.rerouteXY()


print("Plotting file: " + args.file)
w, h = HPGLinput.getSize()
print("Plotting area is {width:.1f}cm x {height:.1f}cm".format(width=w / 10, height=h / 10))
print(" -> Total area:     {area:.1f} cm^2".format(area=w / 10 * h / 10))
movement = sum(HPGLinput.getLength())
print(" -> Total movement: {:.1f} cm".format(movement / 10))

try:
	if args.preview:
		import hpglpreview
		import wx
		app = wx.App(False)
		dialog = hpglpreview.HPGLPreview(HPGLinput, dialog=True)
		if not dialog.ShowModal():
			exit(1)
		cont = 'y'
	else:
		cont = input("continue? (y/n) ")
except KeyboardInterrupt:
	exit(0)
if cont != "y":
	exit(0)

print("Using port: {}".format(args.port))

HPGLdata = HPGLinput.getHPGL()
print("{} characters loaded".format(len(HPGLdata)))

try:
	port = serial.Serial(
		port=args.port,
		baudrate=9600,
		parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
		bytesize=serial.EIGHTBITS,
		rtscts=True,
		dsrdtr=True
	   )

	splitted = HPGLdata.split(";")
	total = len(splitted)

	sys.stdout.write("starting...")

	for i, command in enumerate(splitted):
		sys.stdout.write("\rsending... {percent:.1f}% done ({done}/{total})".format(percent=(i + 1) * 100.0 / total, done=i + 1, total=total))
		sys.stdout.flush()
		# ignore empty
		if not command:
			continue
		port.write(command.encode() + b";")
	port.write("PU0,0;SP0;SP0;")
	sys.stdout.write("\n")
except serial.serialutil.SerialException:
	print("Failed to open port {}.".format(args.port))

__author__ = "doommaster"
