from .commander import *
from .skeleton import *

class Qweboard(Pipe):
	port=9120
	def __init__(self):
		self.network=Component('network')
		self.commander=Commander()
		Pipe.__init__(self, self.network, self.commander)
		self.network.connect(self.commander)
		self.network.port(Qweboard.port)
		Qweboard.port+=1
		self.octave=5
		def octavate(o):
			self.octave+=o
			if self.octave<0: self.octave=0
			if self.octave>10: self.octave=10
		notes={
			'z':  0, 's':  1, 'x':  2, 'd':  3, 'c':  4, 'v':  5,
			'g':  6, 'b':  7, 'h':  8, 'n':  9, 'j': 10, 'm': 11,
			',': 12, 'l': 13, '.': 14, ';': 15, '/': 16,
			'q': 11,
			'w': 12, '3': 13, 'e': 14, '4': 15, 'r': 16, 't': 17,
			'6': 18, 'y': 19, '7': 20, 'u': 21, '8': 22, 'i': 23,
			'o': 24, '0': 25, 'p': 26, '-': 27, '[': 28,
		}
		def command(text):
			c=text.decode('utf-8').split()
			name=c[0]
			sense=int(c[1])
			status=[0x80, 0x90][sense]
			if   name=='PageUp'  : sense and octavate(+1)
			elif name=='PageDown': sense and octavate(-1)
			elif name in notes:
				self.commander.queue(0, 0, 'midi', status, self.octave*12+notes[name], 0x40)
		self.commander.register_command('PageUp'  , command)
		self.commander.register_command('PageDown', command)
		for name in notes: self.commander.register_command(name, command)
