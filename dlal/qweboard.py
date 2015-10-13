from .commander import *
from .skeleton import *

class Qweboard(Pipe):
	def __init__(self, port=9087):
		self.network=Component('network')
		self.commander=Commander()
		Pipe.__init__(self, self.network, self.commander)
		self.network.connect(self.commander)
		self.network.port(port)
		self.octave=5
		def octavate(o): self.octave+=o
		notes={
			'Z':  0, 'S':  1, 'X':  2, 'D':  3, 'C':  4, 'V':  5,
			'G':  6, 'B':  7, 'H':  8, 'N':  9, 'J': 10, 'M': 11,
			',': 12, 'L': 13, '.': 14, ';': 15, '/': 16,
			'Q': 11,
			'W': 12, '3': 13, 'E': 14, '4': 15, 'R': 16, 'T': 17,
			'6': 18, 'Y': 19, '7': 20, 'U': 21, '8': 22, 'I': 23,
			'O': 24, '0': 25, 'P': 26, '-': 27, '[': 28
		}
		def command(text):
			c=text.decode('utf-8').split()
			name=c[0]
			sense=int(c[1])
			status=[0x80, 0x90][sense]
			if   name=='PageUp'  : sense and octavate(+1)
			elif name=='PageDown': sense and octavate(-1)
			else: self.commander.queue(0, 0, 'midi', status, self.octave*12+notes[name], 0x40)
		self.commander.register_command('PageUp'  , command)
		self.commander.register_command('PageDown', command)
		for name in notes: self.commander.register_command(name, command)
