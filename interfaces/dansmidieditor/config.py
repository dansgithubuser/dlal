from __future__ import print_function

try: input=raw_input
except: pass

from controls import AbstractControls

class Controls(AbstractControls):
	def __init__(self):
		AbstractControls.__init__(self)
		self.done=False

	def mouse_motion(self, regex=r'.* x.*' , order=1): self.sequence=self.sequence[:-1]
	def quit        (self, regex=r'.* q'   , order=2): self.done=True
	def reset       (self, regex=r'.* >esc', order=3): self.sequence=[]
	def python      (self, regex=r' <p >p' , order=4): exec(input()); self.reset()
	def print       (self, regex=r'.*'     , order=5): print(''.join([' '+i for i in self.sequence]))

controls=Controls()
