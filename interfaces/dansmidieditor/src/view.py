import os, sys
home=os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(home, '..', '..', '..', 'deps', 'midi'))
import midi

treble=[4, 7, 11, 14, 17]
semitones_per_staff=24

class View:
	def __init__(self, margin=6, text_size=12):
		self.midi=[]
		self.text=''
		self.margin=margin
		self.text_size=text_size
		self.staves=3.9
		self.ticks=5760

	def load(self, path): self.midi=midi.read(path)

	def staves_to_draw(self): return min(int(self.staves)+1, len(self.midi)-1)

	def h_note(self):
		return int(self.h_window/self.staves/semitones_per_staff)

	def y_note(self, staff, note, octave=0):
		y_staff=(staff+1)*self.h_window/self.staves
		return int(y_staff-(note-12*octave)*self.h_note())

	def x_ticks(self, ticks):
		return ticks*self.w_window/self.ticks

	def calculate_octave(self, staff):
		octave=5
		lo=60
		hi=60
		for i in self.midi[staff+1]:
			if i.type!='note': continue
			if i.ticks>=self.ticks: break
			lo=min(lo, i.number)
			hi=max(hi, i.number)
		top=(octave+2)*12
		if hi>top: octave+=(hi-top+11)/12
		bottom=octave*12
		if lo<bottom: octave+=(lo-bottom)/12
		return octave

	def notate_octave(self, octave):
		octave-=5
		if octave>= 1: return '{}va'.format(1+7*octave)
		if octave<=-1: return '{}vb'.format(1-7*octave)
		return ''

	def draw_notes_debug(self, media, octaves):
		for i in range(self.staves_to_draw()):
			for j in self.midi[i+1]:
				if j.type!='note': print(j)
				if j.ticks>=self.ticks: break
				media.line(
					xi=self.x_ticks(j.ticks),
					yi=self.y_note(i, j.number, octaves[i]),
					xf=self.margin,
					yf=self.y_note(i, 24),
				)

	def draw(self, media):
		media.clear()
		self.w_window=media.width()
		self.h_window=media.height()
		#staves
		for i in range(self.staves_to_draw()):
			for j in treble:
				y=self.y_note(i, j)
				media.line(xi=0, xf=self.w_window, y=y, h=0, color=(0, 64, 0))
		media.draw_vertices()
		#octaves
		octaves=[]
		for i in range(self.staves_to_draw()):
			octaves.append(self.calculate_octave(i))
			media.text(
				self.notate_octave(octaves[i]),
				x=self.margin,
				y=self.y_note(i, treble[-1]+2),
				h=self.h_note()*2,
				color=(0, 128, 0),
				middle_y=True,
			)
		#notes
		for i in range(self.staves_to_draw()):
			for j in self.midi[i+1]:
				if j.type!='note': print(j)
				if j.ticks>=self.ticks: break
				media.fill(
					x=self.x_ticks(j.ticks),
					y=self.y_note(i, j.number, octaves[i]),
					w=self.x_ticks(j.duration),
					h=self.h_note(),
					color=(0, 64, 64),
					middle_y=True,
				)
		media.draw_vertices()
		#text
		media.text(self.text, x=self.margin, y=self.h_window-self.margin, h=self.text_size, bottom=True)
		#
		media.display()
