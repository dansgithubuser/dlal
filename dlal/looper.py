from .skeleton import *
from .commander import *
from .liner import *

import json

def track_to_dict(track):
	d=track.to_dict()
	d['class']=track.__class__.__name__
	return d

def track_from_dict(d, component_map):
	track=globals()[d['class']](from_dict=(d, component_map))
	return track

class MidiTrack(Pipe):
	def to_dict(self): return component_to_dict(self, ['input', 'synth', 'container'])

	def __init__(self, input=None, synth=None, from_dict=None):
		if from_dict:
			d, component_map=from_dict
			component_from_dict(self, ['input', 'synth', 'container'], d, component_map)
		else:
			self.input=input
			self.container=Liner()
			self.synth=synth
			self.container.connect(self.synth)
		self.output=self.synth
		Pipe.__init__(self, self.input, self.container, self.synth)

	def drumline(self, text=None, beats=4):
		if not text: text='S '+str(self.container.samples_per_beat//2)+' z . x . z . . . '
		self.container.line(text*((self.container.period_in_samples//self.container.samples_per_beat+beats-1)//beats))

class AudioTrack(Pipe):
	def to_dict(self): return component_to_dict(self, ['input', 'container', 'multiplier'])

	def __init__(self, audio=None, period_in_samples=None, from_dict=None):
		if from_dict:
			d, component_map=from_dict
			component_from_dict(self, ['input', 'container', 'multiplier'], d, component_map)
		else:
			self.input=audio
			self.container=Component('buffer')
			self.multiplier=Component('multiplier')
			self.container.periodic_resize(period_in_samples)
			self.multiplier.connect(self.container)
		self.output=self.input
		self.synth=self.container
		Pipe.__init__(self, self.container, self.multiplier)

class Looper:
	def __init__(self, samples_per_beat, beats, sample_rate=44100, log_2_samples_per_evaluation=6, load=None):
		self.samples_per_beat=samples_per_beat
		self.period_in_samples=beats*samples_per_beat
		self.sample_rate=sample_rate
		self.log_2_samples_per_evaluation=log_2_samples_per_evaluation
		self.system=System()
		if load is not None:
			self.loaded_state=self.system.load(load)
			component_map=self.loaded_state['map']
			self.commander=Commander(component=component_map[self.loaded_state['looper_commander']].transfer_component())
			self.audio=component_map[self.loaded_state['looper_audio']]
			self.tracks=[track_from_dict(i, component_map) for i in self.loaded_state['looper_tracks']]
		else:
			self.commander=Commander()
			self.commander.periodic_resize(samples_per_beat*beats)
			self.audio=Component('audio')
			self.audio.set(sample_rate, log_2_samples_per_evaluation)
			self.system.add(self.audio, self.commander)
			self.tracks=[]

	def save(self, file_name='system.state.txt', extra={}):
		extra.update({
			'looper_commander': self.commander.to_str(),
			'looper_audio': self.audio.to_str(),
			'looper_tracks': [track_to_dict(i) for i in self.tracks],
		})
		self.system.save(file_name, extra)

	def samples_per_evaluation(self): return 1<<self.log_2_samples_per_evaluation

	def add(self, track):
		track.container.samples_per_beat=self.samples_per_beat
		track.container.period_in_samples=self.period_in_samples
		self.commander.queue_command(track.container, 'periodic_match', self.commander.periodic())
		self.commander.queue_add(track)
		self.commander.queue_command(track.synth    , 'label', 'syn{}'.format(len(self.tracks)))
		self.commander.queue_command(track.container, 'label', 'ctr{}'.format(len(self.tracks)))
		self.tracks.append(track)

	def play(self, track, enable, edges_to_wait, input=None):
		if input==None: input=track.input
		self.commander.queue_connect(input, track.output, edges_to_wait=edges_to_wait, enable=enable)

	def record(self, track, enable, edges_to_wait, input=None):
		if input==None: input=track.input
		self.commander.queue_connect(input, track.container, edges_to_wait=edges_to_wait, enable=enable)

	def replay(self, track, enable, edges_to_wait):
		self.commander.queue_connect(track.synth, self.audio, edges_to_wait=edges_to_wait, enable=enable)
