from .skeleton import *
from .commander import *
from .liner import *

class MidiTrack(Pipe):
	def __init__(self, input, synth, period_in_samples, samples_per_beat):
		self.input=input
		self.container=Liner(period_in_samples, samples_per_beat)
		self.synth=synth
		self.output=synth
		Pipe.__init__(self, self.input, self.container, self.synth)
		self.container.resize(period_in_samples)
		self.container.connect(self.synth)

class AudioTrack(Pipe):
	def __init__(self, audio, period_in_samples):
		self.input=audio
		self.container=Component('buffer')
		self.synth=self.container
		self.output=audio
		self.multiplier=Component('multiplier')
		Pipe.__init__(self, self.container, self.multiplier)
		self.container.resize(period_in_samples)
		self.multiplier.connect(self.container)

class Looper:
	def __init__(self, sample_rate=44100, log_2_samples_per_callback=6):
		self.system=System()
		self.commander=Commander()
		self.audio=Component('audio')
		self.audio.set(sample_rate, log_2_samples_per_callback)
		self.system.add(self.audio, self.commander)
		self.tracks=[]

	def add(self, track):
		self.tracks.append(track)
		self.commander.queue_add(track)
		self.commander.queue_command(track.synth    , 'label', len(self.tracks))
		self.commander.queue_command(track.container, 'label', len(self.tracks))

	def play(self, track, enable, edges_to_wait):
		self.commander.queue_connect(track.input, track.output, edges_to_wait=edges_to_wait, enable=enable)

	def record(self, track, enable, edges_to_wait):
		self.commander.queue_connect(track.input, track.container, edges_to_wait=edges_to_wait, enable=enable)

	def replay(self, track, enable, edges_to_wait):
		self.commander.queue_connect(track.synth, self.audio, edges_to_wait=edges_to_wait, enable=enable)

	def reset(self):
		for track in self.tracks:
			self.commander.queue_command(track.container, 'reset')
		self.commander.reset()

	def crop(self):
		for track in self.tracks:
			self.commander.queue_command(track.container, 'crop')
		self.commander.crop()
