from .skeleton import *

import os

class Buffer(Component):
	def __init__(self):
		Component.__init__(self, 'buffer')
		self.known_sounds={}
		for path, folders, files in os.walk(os.path.join('..', '..', 'components', 'buffer', 'sounds')):
			for file in files:
				name, extension=os.path.splitext(file)
				if extension!='.wav': continue
				self.known_sounds[name]=os.path.join(path, file)

	def load_sound(self, file_name, note_number):
		if file_name in self.known_sounds: file_name=self.known_sounds[file_name]
		return self.command('load_sound '+file_name+' '+str(note_number))

	def load_sounds(self):
		known_sounds=self.known_sounds.items()
		known_sounds=sorted(known_sounds, key=lambda x: x[1])
		i=0
		for file_name, path in known_sounds:
			self.load_sound(path, i)
			i+=1
			if i==128: break
