# coding: utf-8

# Instruction name follow http://www.cs.columbia.edu/~sedwards/classes/2016/4840-spring/designs/Chip8.pdf

import re
import struct
import sys

if len(sys.argv) != 3:
	print("Invalid invocation: python compiler.py source result")
	exit()


lineNumber = 1
charStart = 1
charEnd = 1

offset = 0x200
labels = dict()

def error(msg):
	print("Line {0}, char {1}-{2}: {3}.".format(lineNumber, charStart, charEnd, msg))
	exit(1)

def isHex(string, length):
	pattern = "^[0-9A-F]{{1,{0}}}$".format(length)
	return re.match(pattern, string)

def toHex (string, length):
	string = string.strip()
	if (string in labels) and (len(hex(labels[string])) == length + 2):
		return labels[string]

	if not isHex(string, length):
		error("Expected hex number of max length {0} or a valid label".format(length))
	return int(string, 16)

def register (r, pos):
	if re.match("V[0-9A-F]", r):
		return int(r[1], 16) * pos
	else:
		error("Expected register got {0}".format(r))

def isRegister (string):
	return len(string) > 0 and string[0] == "V"

def jp (params):
	size = len(params)
	if (size == 1):
		return 0x1000 + toHex(params[0], 3)
	elif (size == 2 and params[0] == "V0"):
		return 0xB000 + toHex(params[1], 3)
	else:
		error("Invalid JP instruction")



def se (params, neg):
	p1 = params[0]
	p2 = params[1]

	if isRegister(p2):
		return (0x9000 if neg else 0x5000) + register(p1, 0x0100) + register(p2, 0x0010)
	else:
		return (0x4000 if neg else 0x3000) + register(p1, 0x0100) + toHex(p2, 2)

def ld (params):
	p1 = params[0]
	p2 = params[1]

	if isRegister(p1):
		r1 =register(p1, 0x0100)
		if p2 == "DT":
			return 0xF007 + r1
		elif p2 == "K":
			return 0xF00A + r1
		elif p2 == "[I]":
			return 0xF065 + r1
		elif not isRegister(p2):
			return 0x6000 + r1 + toHex(p2, 2)
		else:
			return 0x8000 + r1 + register(p2, 0x0010)
	elif p1 == "I":
		return 0xA000 + toHex(p2, 3)
	elif p1 == "DT":
		return 0xF015 + register(p2, 0x0100)
	elif p1 == "ST":
		return 0xF018 + register(p2, 0x0100)
	elif p1 == "F":
		return 0xF029 + register(p2, 0x0100)
	elif p1 == "B":
		return 0xF033 + register(p2, 0x0100)
	elif p1 == "[I]":
		return 0xF055 + register(p2, 0x0100)
	else:
		error("Invalid LD instruction")

def add (params):
	if (params[0] == "I"):
		return 0xF01E + register(params[1], 0x0100)
	else:
		if (isRegister(params[1])):
			return 0x8004 + register(params[0], 0x0100) + register(params[1], 0x0010)
		else:
			return 0x7000 + register(params[0], 0x0100) + toHex(params[1], 2)

encoder = {
	"SYS"	: lambda x: toHex(x[0], 3),
	"CLS"	: lambda x: 0x00E0,
	"RET"	: lambda x: 0x00EE,
	"JP" 	: lambda x: jp(x),
	"CALL"	: lambda x: 0x2000 + toHex(x[0], 3),
	"SE"	: lambda x: se(x, False),
	"SNE"	: lambda x: se(x, True),
	"LD"	: lambda x: ld(x),
	"OR"	: lambda x: 0x8001 + register(x[0], 0x0100) + register(x[1], 0x0010),
	"AND"	: lambda x: 0x8002 + register(x[0], 0x0100) + register(x[1], 0x0010),
	"XOR"	: lambda x: 0x8003 + register(x[0], 0x0100) + register(x[1], 0x0010),
	"ADD"	: lambda x: add(x),
	"SUB"	: lambda x: 0x8005 + register(x[0], 0x0100) + register(x[1], 0x0010),
	"SHR"	: lambda x: 0x8006 + register(x[0], 0x0100) + register(x[1], 0x0010),
	"SUBN"	: lambda x: 0x8007 + register(x[0], 0x0100) + register(x[1], 0x0010),
	"SHL"	: lambda x: 0x800E + register(x[0], 0x0100) + register(x[1], 0x0010),
	"RND"	: lambda x: 0xC000 + register(x[0], 0x0100) + toHex(x[1], 2),
	"DRW"	: lambda x: 0xD000 + register(x[0], 0x0100) + register(x[1], 0x0010) + toHex(x[2], 1),
	"SKP"	: lambda x: 0xE09E + register(x[0], 0x0100),
	"SKNP"	: lambda x: 0xE0A1 + register(x[0], 0x0100),
}

def handleInstruction (instruction):
	sp = instruction.split()
	if not sp[0] in encoder:
		if (len(sp) == 1):
			if (isHex(sp[0], 2)):
				return toHex(sp[0], 2) * 0x0100
			if (isHex(sp[0], 4)):
				return toHex(sp[0], 4)
		error("Unknown command {0}".format(sp[0]))

	try:
		return encoder[sp[0]](sp[1:])
	except IndexError:
		error("Invalid number of paramaters for {0}".format(sp[0]))

compiled = []
with open(sys.argv[1], 'r') as f:
	# parse for labels
	for line in f.read().splitlines():
		line = line.split('//')[0].strip()
		if not line:
			continue
		if line[0] == "~":
			labels[line.strip().upper()] = offset
			continue

		for instruction in line.split(";"):
			if (not instruction) or instruction.isspace():
				continue
			offset += 2
	f.seek(0)

	# parse for instructions
	for line in f.read().upper().splitlines():
		charStart = 1
		line = line.split('//')[0].strip()
		if (not line) or (line[0] == '~'):
			lineNumber = lineNumber + 1
			continue

		for instruction in line.split(";"):
			if (not instruction) or instruction.isspace():
				continue
			charEnd = charStart + len(instruction) - 1
			compiled.append(handleInstruction(instruction))
			charStart = charEnd + 2
		lineNumber = lineNumber + 1

with open(sys.argv[2], 'wb') as f:
	for i in compiled:
		f.write(struct.pack(">H", i))
