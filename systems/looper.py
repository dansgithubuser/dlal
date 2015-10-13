import dlal, atexit

period=8*2*32000
edges_to_wait=0
track=0

#looper
looper=dlal.Looper()
looper.system.set('track', str(track))
looper.system.set('wait', str(edges_to_wait))

#midi
midi=dlal.Component('midi')
ports=[x for x in midi.ports().split('\n') if len(x)]
if len(ports): midi.open(ports[0])

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

def reset():
	looper.commander.queue_command(looper.commander, 'resize', 0)

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

def reset_on_midi():
	looper.commander.queue_command(tracks[track].container, 'reset_on_midi')

def crop():
	looper.commander.queue_command(tracks[track].container, 'crop')

def track_match():
	period, phase=looper.commander.get().split()
	looper.commander.queue_command(tracks[track].container, 'resize', period)
	looper.commander.queue_command(tracks[track].container, 'set_phase', phase)

def generate_standard_command(function, sense):
	def command(): function(looper, tracks[track], sense, edges_to_wait)
	return command

commands={
	'1': (add_midi, 'add midi track'),
	'[': (commander_match, 'match commander to current track'),
	']': (reset, 'reset commander'),
	'U': (track_next, 'next track'),
	'J': (track_prev, 'prev track'),
	'I': (wait_more, 'wait more'),
	'K': (wait_less, 'wait less'),
	'Return': (reset_on_midi, 'reset track on midi'),
	'Space': (crop, 'crop track'),
	'\\': (track_match, 'match current track to commander'),
	'Q': (generate_standard_command(dlal.Looper.record, False), 'stop track record'),
	'A': (generate_standard_command(dlal.Looper.record, True ), 'start track record'),
	'W': (generate_standard_command(dlal.Looper.play  , False), 'stop track play'),
	'S': (generate_standard_command(dlal.Looper.play  , True ), 'start track play'),
	'E': (generate_standard_command(dlal.Looper.replay, False), 'stop track replay'),
	'D': (generate_standard_command(dlal.Looper.replay, True ), 'start track replay'),
}

def command(text):
	c=text.decode('utf-8').split()
	name=c[0]
	sense=int(c[1])
	if sense: commands[name][0]()
for name in commands: looper.commander.register_command(name, command)

def go():
	looper.audio.start()
	atexit.register(lambda: looper.audio.finish())

def help():
	for name, command in commands.items():
		print('{0}: {1}'.format(name, command[1]))

print('use the go function to start audio processing')
print('use the help function for softboard key listing')
