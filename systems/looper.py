import dlal, os, sys

samples_per_beat=32000

period=8*2*samples_per_beat
edges_to_wait=0
track=0
sequence=None

#looper
looper=dlal.Looper()
looper.system.set('track', str(track))
looper.system.set('wait', str(edges_to_wait))
looper.system.set('sequence', 'none')

#midi
midi=dlal.Component('midi')
qweboard=dlal.Qweboard()
qweboard.connect(midi)
looper.system.add(qweboard)

#network
network=dlal.Component('network')
network.connect(looper.commander)
looper.system.add(network)

#commands
tracks=[]

def add_midi():
	track=dlal.MidiTrack(midi, dlal.Fm(), period, samples_per_beat)
	global tracks
	tracks.append(track)
	looper.add(track)

def add_metronome():
	track=dlal.MidiTrack(midi, dlal.Fm(), period, samples_per_beat)
	track.drumline()
	track.synth.load(os.path.join(dlal.root, 'components', 'fm', 'settings', 'snare.txt'))
	global tracks
	tracks.append(track)
	looper.add(track)

def commander_match():
	period, phase=tracks[track].container.get().split()
	looper.commander.queue_command(looper.commander, 'resize', period)
	looper.commander.queue_command(looper.commander, 'set_phase', phase)

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
	looper.commander.queue_command(tracks[track].container, 'crop')

def track_match():
	period, phase=looper.commander.get().split()
	looper.commander.queue_command(tracks[track].container, 'resize', period)
	looper.commander.queue_command(tracks[track].container, 'set_phase', phase)

def track_reset():
	looper.commander.queue_command(tracks[track].container, 'set_phase', 0, edges_to_wait=edges_to_wait)

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
	('1', (add_midi, 'add midi track')),
	('2', (add_metronome, 'add metronome midi track')),
	('J', (track_next, 'next track')),
	('U', (track_prev, 'prev track')),
	('K', (wait_more, 'wait more')),
	('I', (wait_less, 'wait less')),
	('Return', (track_reset_on_midi, 'reset track on midi')),
	('Space', (track_crop, 'crop track')),
	('[', (commander_match, 'match commander to current track')),
	(']', (track_match, 'match current track to commander')),
	('F', (track_reset, 'reset track')),
	('Q', (generate_standard_command(dlal.Looper.record, False), 'stop track record')),
	('A', (generate_standard_command(dlal.Looper.record, True ), 'start track record')),
	('W', (generate_standard_command(dlal.Looper.play  , False), 'stop track play')),
	('S', (generate_standard_command(dlal.Looper.play  , True ), 'start track play')),
	('E', (generate_standard_command(dlal.Looper.replay, False), 'stop track replay')),
	('D', (generate_standard_command(dlal.Looper.replay, True ), 'start track replay')),
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
	for name, command in commands:
		print('{0}: {1}'.format(name, command[1]))

go, quit, ports=dlal.standard_system_functionality(looper.system, looper.audio, midi, ['use the help function for softboard key listing'])

class Quitter():
	def __repr__(self): quit()

qq=Quitter()
