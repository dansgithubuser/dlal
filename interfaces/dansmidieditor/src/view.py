import os, sys
home=os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(home, '..', '..', '..', 'deps', 'midi'))
import midi

class View:
	def __init__(self, margin=6, text_size=12):
		self.midi=[]
		self.text=''
		self.margin=margin
		self.text_size=text_size
		self.staves=4

	def load(self, path): self.midi=midi.read(path)

	def y_note(self, staff, note, height):
		semitones_per_staff=24
		y_staff=(staff+1)*height/self.staves
		y_note=int(y_staff-note*height/self.staves/semitones_per_staff)
		return y_note

	def draw(self, media):
		media.clear()
		#staves
		treble=[4, 7, 11, 14, 17]
		bass=[7, 11, 14, 17, 21]
		for i in range(int(self.staves)+1):
			clef=treble
			for j in clef:
				y=self.y_note(i, j, media.height())
				media.line(xi=0, yi=y, xf=media.width(), yf=y, color=(0, 64, 0))
		media.draw_vertices()
		#notes
		for i in self.midi:
			for j in i:
				if j.type!='note': continue
				media.fill(x=j.ticks/8, y=8*j.number, w=j.duration/8, h=8)
		#text
		media.text(self.margin, media.height()-self.margin-self.text_size, self.text_size, self.text)
		#
		media.display()
