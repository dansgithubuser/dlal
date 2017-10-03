import os, sys
home=os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(home, '..', '..', '..', 'deps', 'midi'))
import midi

class View:
	def __init__(self, margin=6, text_size=12):
		self.midi=midi.read(os.path.join(home, '..', '..', '..', 'deps', 'midi', 'trans.mid'))
		self.text=''
		self.margin=margin
		self.text_size=text_size

	def draw(self, media):
		media.clear()
		media.text(self.margin, media.height()-self.margin-self.text_size, self.text_size, self.text)
		for i in self.midi:
			for j in i:
				if j.type!='note': continue
				media.fill(x=j.ticks/8, y=8*j.number, w=j.duration/8, h=8)
		media.display()
