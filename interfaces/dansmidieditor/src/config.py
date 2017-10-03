from controls import AbstractControls
from view import View

class Controls(AbstractControls):
	def __init__(self):
		AbstractControls.__init__(self)
		self.done=False
		self.view=View()

	def prettied_sequence(self):
		r=[]
		skip=False
		for i, v in enumerate(self.sequence):
			if skip: skip=False; continue
			u=self.sequence[i+1] if i+1<len(self.sequence) else '  '
			if v[0]=='<' and u[0]=='>' and v[1]==u[1]: r.append(v[1]); skip=True
			else: r.append(v)
		return ''.join(r)

	def mouse_motion (self, regex=r'.* x.*' , order=  1): self.sequence=self.sequence[:-1]
	def quit         (self, regex=r'.* q'   , order=  2): self.done=True
	def reset        (self, regex=r'.* >Esc', order=  3): self.sequence=[]; self.show_sequence()
	def show_sequence(self, regex=r'.*'     , order=999): self.view.text=self.prettied_sequence()

controls=Controls()
