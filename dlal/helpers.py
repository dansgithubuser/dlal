from .skeleton import *
from .qweboard import *

import sys

def standard_system_functionality(audio, midi=None, test=False):
	import atexit
	def go():
		audio.start()
		atexit.register(lambda: audio.finish())
		if not test: print('audio processing going')
	if not test: print('use the go function to start audio processing')
	if len(sys.argv)>1 and sys.argv[1]=='-g':
		print('-g option specified -- starting audio processing')
		go()
	if test: go()
	ports=None
	if midi and not test:
		ports=[x for x in midi.ports().split('\n') if len(x)]
		if len(ports):
			print('opening midi port '+ports[0])
			midi.open(ports[0])
	return go, ports

def raw_to_unsigned_8_bit_pcm(input_file_name, output_file_name):
	with open(input_file_name) as file: samples=file.read().split()
	with open(output_file_name, 'wb') as file:
		for sample in samples: file.write(chr(int((float(sample)+1)*63)).encode())

def tunefish_path():
	file_path=os.path.split(os.path.realpath(__file__))[0]
	vst_folder=os.path.join(
		file_path, '..', 'components', 'vst', 'deps', 'tunefish-v4.0.1'
	)
	if   platform.system()=='Windows':
		if sys.maxsize>2**32:
			vst_file='tunefish4-64.dll'
		else:
			vst_file='tunefish4-32.dll'
	elif platform.system()=='Darwin':
		vst_file  ='tunefish4.vst'
	elif platform.system()=='Linux':
		if sys.maxsize>2**32:
			vst_file='tunefish4-64.so'
		else:
			vst_file='tunefish4-32.so'
	return os.path.join(vst_folder, vst_file)

class SimpleSystem:
	def __init__(self, components, midi_receivers=None, outputs=None, test=False, test_duration=10):
		self.sample_rate=44100
		self.test=test
		#create
		self.system=System()
		if not self.test: self.qweboard=Qweboard()
		self.midi=Component('midi')
		if self.test: self.midi.midi(0x90, 0x3C, 0x40)
		self.components=components
		if self.test:
			self.audio=Component('raw')
			self.audio.duration(test_duration)
		else:
			self.audio=Component('audio')
		#command
		self.audio.set(self.sample_rate, 6)
		#add
		self.system.add(self.audio, slot=1 if self.test else 0)
		if not self.test: self.system.add(self.qweboard)
		self.system.add(self.midi, *self.components)
		#connect
		if not self.test: self.qweboard.connect(self.midi)
		x=components
		if midi_receivers!=None: x=midi_receivers
		for component in x: self.midi.connect(component)
		x=components
		if outputs!=None: x=outputs
		for component in x: component.connect(self.audio)

	def standard_system_functionality(self):
		return standard_system_functionality(
			self.audio, self.midi, self.test
		)
