from .skeleton import *

g_notes={
	'z': 0, 's': 1, 'x': 2, 'd': 3, 'c': 4, 'v': 5,
	'g': 6, 'b': 7, 'h': 8, 'n': 9, 'j': 10, 'm': 11, ',': 12,
	'w': 12, '3': 13, 'e': 14, '4': 15, 'r': 16, 't': 17,
	'6': 18, 'y': 19, '7': 20, 'u': 21, '8': 22, 'i': 23, 'o': 24
}

class Liner(Component):
	def __init__(self):
		Component.__init__(self, 'liner')

	def line(self, text):
		stride=0
		octave=5
		sample=0
		text=text.split()
		i=0
		while i<len(text):
			t=text[i]
			i+=1
			if   t=='S': stride=int(text[i]); i+=1
			elif t=='O': octave=int(text[i]); i+=1
			else:
				notes=[]
				nextSample=sample+stride
				for j in range(len(t)):
					if t[j]=='.':
						if j!=0:
							nextSample+=stride
					else: notes.append(12*octave+g_notes[t[j]])
				for note in notes:
					def m(sample, command, note):
						return 'midi {0} {1:x} {2:x} 40'.format(sample, command, note)
					self.command(m(sample    , 0x90, note))
					self.command(m(nextSample, 0x80, note))
				sample=nextSample
