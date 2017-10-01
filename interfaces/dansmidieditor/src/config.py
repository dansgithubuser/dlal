from controls import AbstractControls
from view import View

class Controls(AbstractControls):
	def __init__(self):
		AbstractControls.__init__(self)
		self.done=False
		self.view=View()

	def mouse_motion(self, regex=r'.* x.*' , order=  1): self.sequence=self.sequence[:-1]
	def quit        (self, regex=r'.* q'   , order=  2): self.done=True
	def reset       (self, regex=r'.* >Esc', order=  3): self.sequence=[]

controls=Controls()
