class AbstractControls:
	def __init__(self):
		self.sequence=[]
		import inspect
		self.controls=[]
		for i in dir(self):
			a=getattr(self, i)
			if not callable(a): continue
			if any([j not in inspect.getargspec(a).args for j in ['regex', 'order']]): continue
			defaults=inspect.getcallargs(a)
			self.controls.append((defaults['regex'], i, defaults['order']))
		self.controls=sorted(self.controls, key=lambda i: i[2])
		self.controls=[i[:2] for i in self.controls]

	def input(self, word):
		self.sequence.append(word)
		import re
		for regex, method in self.controls:
			s=''.join([' '+i for i in self.sequence])
			m=re.match(regex, s)
			#print(regex, s, 'm' if m else '')
			if m:
				getattr(self, method)()
				break
