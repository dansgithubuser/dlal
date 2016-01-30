import dlal

period=8*2*32000
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
ports=[x for x in midi.ports().split('\n') if len(x)]
if len(ports): midi.open(ports[0])
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
	track=dlal.MidiTrack(midi, dlal.Fm(), period, 32000)
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

def go():
	looper.audio.start()
	print('audio processing going')

def quit():
	looper.audio.finish()
	looper.system.demolish()
	import sys
	sys.exit()

class Quitter():
	def __repr__(self):
		quit()
		return 'quit'

qq=Quitter()

def help():
	for name, command in commands:
		print('{0}: {1}'.format(name, command[1]))

print('use the go function to start audio processing')
print('use the quit function or qq to quit')
print('use the help function for softboard key listing')

if len(sys.argv)>1 and sys.argv[1]=='-g':
	print('-g option specified -- starting audio processing')
	go()
