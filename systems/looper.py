import dlal, os, sys

samples_per_beat=32000

period=8*2*samples_per_beat
edges_to_wait=0
input=0
track=0
sequence=None

#looper
looper=dlal.Looper()
looper.system.set('wait', str(edges_to_wait))
looper.system.set('input', str(input))
looper.system.set('track', str(track))
looper.system.set('sequence', 'none')

#inputs
class Input:
	def __init__(self):
		self.midi=dlal.Component('midi')
		self.qweboard=dlal.Qweboard()
		looper.commander.queue_connect(self.qweboard, self.midi, enable=True)
		looper.commander.queue_add(self.qweboard)
inputs=[]

#network
network=dlal.Component('network')
network.connect(looper.commander)
looper.system.add(network)

#commands
tracks=[]

def add_input():
	looper.system.set('input {}'.format(len(inputs)), 'port {}'.format(dlal.Qweboard.port))
	inputs.append(Input())

def add_midi():
	track=dlal.MidiTrack(inputs[input].midi, dlal.Sonic(), period, samples_per_beat)
	tracks.append(track)
	looper.add(track)

def add_metronome():
	track=dlal.MidiTrack(inputs[input].midi, dlal.Sonic(), period, samples_per_beat)
	track.drumline()
	track.synth.load(os.path.join(dlal.root, 'components', 'sonic', 'settings', 'snare.txt'))
	tracks.append(track)
	looper.add(track)

def add_audio():
	track=dlal.AudioTrack(looper.audio, period)
	tracks.append(track)
	looper.add(track)

def input_next():
	global input
	if input+1<len(inputs):
		input+=1
		looper.system.set('input', str(input))

def input_prev():
	global input
	if input>0:
		input-=1
		looper.system.set('input', str(input))

def track_next():
	global track
	if track+1<len(tracks):
		track+=1
		looper.system.set('track', str(track))

def track_prev():
	global track
	if track>0:
		track-=1
		looper.system.set('track', str(track))

def wait_more():
	global edges_to_wait
	edges_to_wait+=1
	looper.system.set('wait', str(edges_to_wait))

def wait_less():
	global edges_to_wait
	if edges_to_wait>0:
		edges_to_wait-=1
		looper.system.set('wait', str(edges_to_wait))

def track_reset_on_midi():
	looper.commander.queue_command(tracks[track].container, 'reset_on_midi')

def track_crop():
	looper.commander.queue_command(tracks[track].container, 'periodic_crop')

def commander_match():
	period, phase=tracks[track].container.periodic_get().split()
	looper.commander.queue_command(looper.commander, 'periodic_resize', period)
	looper.commander.queue_command(looper.commander, 'periodic_set_phase', phase)

def track_match():
	period, phase=looper.commander.periodic_get().split()
	looper.commander.queue_command(tracks[track].container, 'periodic_resize', period)
	looper.commander.queue_command(tracks[track].container, 'periodic_set_phase', phase)

def track_reset():
	looper.commander.queue_command(tracks[track].container, 'periodic_set_phase', 0, edges_to_wait=edges_to_wait)

def generate_standard_command(function, sense):
	def command(): function(looper, tracks[track], sense, edges_to_wait)
	return command

def sequence_start():
	global sequence
	sequence=[]
	looper.system.set('sequence', '-')

def sequence_commit():
	for name in sequence: commands_dict[name][0]()
	sequence_cancel()

def sequence_cancel():
	global sequence
	sequence=None
	looper.system.set('sequence', 'none')

commands=[
	('F1', (add_input, 'add input')),
	('F5', (add_midi, 'add midi track')),
	('F6', (add_metronome, 'add metronome midi track')),
	('F7', (add_audio, 'add audio track')),
	('j', (input_next, 'next input')),
	('u', (input_prev, 'prev input')),
	('k', (track_next, 'next track')),
	('i', (track_prev, 'prev track')),
	('l', (wait_more, 'wait more')),
	('o', (wait_less, 'wait less')),
	('Return', (track_reset_on_midi, 'reset track on midi')),
	('Space', (track_crop, 'crop track')),
	('[', (commander_match, 'match commander to current track')),
	(']', (track_match, 'match current track to commander')),
	('f', (track_reset, 'reset track')),
	('q', (generate_standard_command(dlal.Looper.record, False), 'stop track record')),
	('a', (generate_standard_command(dlal.Looper.record, True ), 'start track record')),
	('w', (generate_standard_command(dlal.Looper.play  , False), 'stop track play')),
	('s', (generate_standard_command(dlal.Looper.play  , True ), 'start track play')),
	('e', (generate_standard_command(dlal.Looper.replay, False), 'stop track replay')),
	('d', (generate_standard_command(dlal.Looper.replay, True ), 'start track replay')),
	(',', (sequence_start, 'start sequence')),
	('.', (sequence_commit, 'commit sequence')),
	('/', (sequence_cancel, 'cancel sequence')),
]
commands_dict=dict(commands)

def command(text):
	c=text.decode('utf-8').split()
	name=c[0]
	sense=int(c[1])
	if not sense: return
	if sequence!=None and name not in ['.', '/']:
		if name!=',':
			sequence.append(name)
			looper.system.set('sequence', '-'.join(sequence))
		return
	if name in commands_dict: commands_dict[name][0]()
for name in commands_dict: looper.commander.register_command(name, command)

def help():
	print('functions:')
	print('\thelp: print this help')
	print('qweboard commands:')
	for name, command in commands:
		print('\t{0}: {1}'.format(name, command[1]))

add_input()
go, ports=dlal.standard_system_functionality(looper.audio, inputs[0].midi)

for i in 'F5 s d'.split(): commands_dict[i][0]()

help()
