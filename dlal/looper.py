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
		self.container.periodic_resize(period_in_samples)
		self.container.connect(self.synth)

	def drumline(self, text=None, beats=4):
		if not text: text='S '+str(self.container.samples_per_beat//2)+' z . x . z . . . '
		self.container.line(text*((self.container.period_in_samples//self.container.samples_per_beat+beats-1)//beats))

class AudioTrack(Pipe):
	def __init__(self, audio, period_in_samples):
		self.input=audio
		self.container=Component('buffer')
		self.synth=self.container
		self.output=audio
		self.multiplier=Component('multiplier')
		Pipe.__init__(self, self.container, self.multiplier)
		self.container.periodic_resize(period_in_samples)
		self.multiplier.connect(self.container)

class Looper:
	def __init__(self, sample_rate=44100, log_2_samples_per_evaluation=6):
		self.sample_rate=sample_rate
		self.log_2_samples_per_evaluation=log_2_samples_per_evaluation
		self.system=System()
		self.commander=Commander()
		self.audio=Component('audio')
		self.audio.set(sample_rate, log_2_samples_per_evaluation)
		self.system.add(self.audio, self.commander)
		self.tracks=[]

	def samples_per_evaluation(self): return 1<<self.log_2_samples_per_evaluation

	def add(self, track):
		self.commander.queue_add(track)
		self.commander.queue_command(track.synth    , 'label', len(self.tracks))
		self.commander.queue_command(track.container, 'label', len(self.tracks))
		self.tracks.append(track)

	def play(self, track, enable, edges_to_wait):
		self.commander.queue_connect(track.input, track.output, edges_to_wait=edges_to_wait, enable=enable)

	def record(self, track, enable, edges_to_wait):
		self.commander.queue_connect(track.input, track.container, edges_to_wait=edges_to_wait, enable=enable)

	def replay(self, track, enable, edges_to_wait):
		self.commander.queue_connect(track.synth, self.audio, edges_to_wait=edges_to_wait, enable=enable)
