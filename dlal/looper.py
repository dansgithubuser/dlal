from .skeleton import *
from .commander import *
from .liner import *

class MidiTrack(Pipe):
	def __init__(self, input, synth):
		self.input=input
		self.container=Liner()
		self.synth=synth
		self.output=synth
		Pipe.__init__(self, self.input, self.container, self.synth)
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
	def __init__(self, samples_per_beat, beats, sample_rate=44100, log_2_samples_per_evaluation=6):
		self.samples_per_beat=samples_per_beat
		self.period_in_samples=beats*samples_per_beat
		self.sample_rate=sample_rate
		self.log_2_samples_per_evaluation=log_2_samples_per_evaluation
		self.system=System()
		self.commander=Commander()
		self.commander.periodic_resize(samples_per_beat*beats)
		self.audio=Component('audio')
		self.audio.set(sample_rate, log_2_samples_per_evaluation)
		self.system.add(self.audio, self.commander)
		self.tracks=[]

	def samples_per_evaluation(self): return 1<<self.log_2_samples_per_evaluation

	def add(self, track):
		track.container.samples_per_beat=self.samples_per_beat
		track.container.period_in_samples=self.period_in_samples
		self.commander.queue_command(track.container, 'periodic_match', self.commander.periodic())
		self.commander.queue_add(track)
		self.commander.queue_command(track.synth    , 'label', 'syn{}'.format(len(self.tracks)))
		self.commander.queue_command(track.container, 'label', 'ctr{}'.format(len(self.tracks)))
		self.tracks.append(track)

	def play(self, track, enable, edges_to_wait):
		self.commander.queue_connect(track.input, track.output, edges_to_wait=edges_to_wait, enable=enable)

	def record(self, track, enable, edges_to_wait):
		self.commander.queue_connect(track.input, track.container, edges_to_wait=edges_to_wait, enable=enable)

	def replay(self, track, enable, edges_to_wait):
		self.commander.queue_connect(track.synth, self.audio, edges_to_wait=edges_to_wait, enable=enable)
