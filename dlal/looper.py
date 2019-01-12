from .skeleton import *
from .commander import *
from .liner import *

import collections
import json
import random

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

	def drumline(self, snare_note=0x3c, kick_note=0x3e, ride_note=0x40):
		n_bars=4
		pattern=[random.randint(0, n_bars-1) for i in range(n_bars)]
		def sensible_number():
			r=random.randint(1, 100)
			for i in range(7, 2, -1):
				if r%(i*i//3)==0: return i
			return 4
		beats_per_bar=sensible_number()
		def make_strong_beats(beats):
			groups=[]
			while beats>4:
				group=random.randint(2, 3)
				beats-=group
				groups.append(group)
			if beats==4: groups.extend([2, 2])
			elif beats==3: groups.append(3)
			result=[0]
			for group in groups: result.append(result[-1]+group)
			return result
		strong_beats=make_strong_beats(beats_per_bar)
		divisions_per_beat=sensible_number()
		class Notes(list): pass
		Note=collections.namedtuple('Note', ['number', 'velocity'])
		def random_notes(beat, division):
			result=Notes()
			velocity=0x3f if division==0 else 0x1f
			if random.randint(0, 2)==0: result.append(Note(ride_note, velocity))
			if beat==0 and division==0:
				result.append(Note(kick_note, 0x7f))
			elif random.randint(0, 8)==0:
				result.append(Note(kick_note, velocity))
			if division==0 and beat!=0 and beat in strong_beats:
				result.append(Note(snare_note, 0x5f))
			elif random.randint(0, 4)==0: result.append(Note(snare_note, velocity))
			return result
		bars=[]
		for i in range(n_bars):
			bar=[
				[random_notes(j, k) for k in range(divisions_per_beat)]
				for
				j in range(beats_per_bar)
			]
			bars.append(bar)
		for i in range(n_bars):
			pattern[i]=bars[pattern[i]]
		class Accumulator:
			def __init__(self): self.value=0
			def add(self, addend): self.value+=addend
		sample=Accumulator()
		def traverse(pattern, divisor=1):
			if isinstance(pattern, Notes):
				duration=self.container.period_in_samples//divisor
				for i in pattern:
					self.container.midi_event(sample.value,
						0x90, i.number, i.velocity)
					self.container.midi_event(sample.value+3*duration//4,
						0x80, i.number, i.velocity)
				sample.add(duration)
			else:
				for i in pattern: traverse(i, divisor*len(pattern))
		self.container.clear()
		traverse(pattern)

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
	def __init__(self, samples_per_beat, beats, sample_rate=44100, log_2_samples_per_evaluation=7, load=None):
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
