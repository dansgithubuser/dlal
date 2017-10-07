import os, sys
home=os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(home, '..', '..', '..', 'deps', 'midi'))
import midi

staff=[7, 11, 14, 17, 21, 28, 31, 35, 38, 41]
semitones_per_staff=48

class View:
	def __init__(self, margin=6, text_size=12):
		self.midi=[]
		self.text=''
		self.margin=margin
		self.text_size=text_size
		self.staves=4
		self.ticks=5760

	def load(self, path): self.midi=midi.read(path)

	def staves_to_draw(self): return int(self.staves)+1

	def h_note(self, h_window):
		return h_window/self.staves/semitones_per_staff

	def y_note(self, staff, note, h_window):
		y_staff=(staff+1)*h_window/self.staves
		y_note=int(y_staff-note*self.h_note(h_window))
		return y_note

	def x_ticks(self, ticks, w_window):
		return ticks*w_window/self.ticks

	def draw(self, media):
		media.clear()
		#staves
		for i in range(self.staves_to_draw()):
			for j in staff:
				y=self.y_note(i, j, media.height())
				media.line(xi=0, xf=media.width(), y=y, h=0, color=(0, 64, 0))
		media.draw_vertices()
		#notes
		for i in range(min(len(self.midi)-1, self.staves_to_draw())):
			for j in self.midi[i+1]:
				if j.type!='note': print(j)
				media.fill(
					x=self.x_ticks(j.ticks, media.width()),
					y=self.y_note(i, j.number, media.height())-self.h_note(media.height()),
					w=self.x_ticks(j.duration, media.width()),
					h=self.h_note(media.height()),
				)
		#text
		media.text(self.margin, media.height()-self.margin-self.text_size, self.text_size, self.text)
		#
		media.display()
