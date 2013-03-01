#!/usr/bin/python3
import os
import collections
import ctypes

def colprint(msg, colcode):
	print("\x1b[" + str(colcode) + "m" + msg + "\x1b[m")

def fatal(msg):
	colprint(msg, 31)
	print_nonfatals("Nonfatal errors before this error:")
	sys.exit(1)

#store all non-fatal errors
nonfatals = []
def print_nonfatals(msg = "Nonfatal errors"):
	if len(nonfatals) > 0:
		print(msg)
		for nonfatal in nonfatals:
			print(nonfatal)

def nonfatal(msg):
	colprint(msg, 33)
	nonfatals.append(msg)

def info(msg):
	colprint(msg, 36)

__all__ = ["monotonic_time"]
CLOCK_MONOTONIC = 1 # see <linux/time.h>
class timespec(ctypes.Structure):
    _fields_ = [
        ('tv_sec', ctypes.c_long),
        ('tv_nsec', ctypes.c_long)
    ]

librt = ctypes.CDLL('librt.so.1', use_errno=True)
clock_gettime = librt.clock_gettime
clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]

def monotonic_time():
    t = timespec()
    if clock_gettime(CLOCK_MONOTONIC, ctypes.pointer(t)) != 0:
        errno_ = ctypes.get_errno()
        raise OSError(errno_, os.strerror(errno_))
    return t.tv_sec + t.tv_nsec * 1e-9

#returns runtime of command, as float, in seconds
def run_command(command, vis = True):
	if vis:
		print(command)

	t_begin = monotonic_time()
	exitcode = os.system(command)
	t_end = monotonic_time()

	if exitcode == 0:
		return t_end - t_begin
	else:
		nonfatal("command \"" + command + "\" failed with exit code " + exitcode)
		return None

class resulttable:
	def __init__(self):
		self.data = {}
		self.rows = collections.OrderedDict()
		self.cols = collections.OrderedDict()

	def insval(self, row, col, v):
		if v == None:
			return

		#update column and row indices with their maximum field size values
		if not row in self.rows:
			self.rows[row] = max(len(str(row)), len(str(v)))
			self.data[row] = collections.OrderedDict()
		else:
			self.rows[row] = max(self.rows[row], len(str(v)))

		if not col in self.cols:
			self.cols[col] = max(len(str(col)), len(str(v)))
		else:
			self.cols[col] = max(self.cols[col], len(str(v)))

		#store the value
		self.data[row][col] = v

	def getval(self, row, col):
		if not row in self.rows or not col in self.data[row]:
			return None
		else:
			return self.data[row][col]

	def getvalstr(self, row, col, printnone = "none"):
		val = self.getval(row, col)
		if val == None:
			return printnone
		else:
			return str(val)

	def getline(self, source, sep, padding):
		line = ""
		for col in self.cols:
			data = str(source(col))
			if padding:
				line += data.ljust(self.cols[col])
			else:
				line += data
			line += sep

		return line[:-len(sep)]

	def gettitle(self, sep = " | ", padding = True):
		return self.getline(lambda x: x, sep, padding)

	def getempty(self, sep = " | ", padding = True):
		return self.getline(lambda x: "", sep, padding)

	def getbody(self, printnone = "none", sep = " | ", padding = True):
		body = ""
		for row in self.rows:
			body += self.getline(lambda x: self.getvalstr(row, x, printnone), sep, padding) + "\n"
		return body[:-1]

	def print(self, desc, printnone="none"):
		print(desc + "\n")
		print(self.gettitle())
		print(self.getempty())
		print(self.getbody(printnone))
	
	def to_csv(self, filename):
		f = open(filename, 'w')
		f.write(self.gettitle(",") + "\n")
		f.write(self.getbody("", ",") + "\n")
		f.close()
	
	def sort(self):
		newrows = collections.OrderedDict()
		for r in sorted(self.rows):
			newrows[r] = self.rows[r]
		self.rows = newrows
