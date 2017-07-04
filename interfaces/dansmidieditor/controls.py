class Controls:
	def __init__(self, filename):
		globals={'controls': None}
		with open(filename) as file: exec(file.read(), globals)
		self.controls=globals['controls']
		self.sequence=[]

	def input(self, word, api=None):
		self.sequence.append(word)
		import re
		for regex, script in self.controls:
			if re.match(regex, ''.join([' '+i for i in self.sequence])):
				exec(script)
				break

