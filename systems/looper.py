import dlal, atexit

max_track_samples=64000*8
samples_per_beat=32000
edges_to_wait=0
track=0

#looper
looper=dlal.Looper()
looper.commander.set_callback(dlal.report)

#midi
midi=dlal.Component('midi')
ports=[x for x in midi.ports().split('\n') if len(x)]
if len(ports): midi.open(ports[0])

#network
network=dlal.Component('network')
network.open(9089)
network.connect(looper.commander)
looper.system.add(network)

#commands
tracks=[]

def command_add_midi():
	track=dlal.MidiTrack(
		midi,
		dlal.Fm(),
		max_track_samples,
		samples_per_beat
	)
	global tracks
	tracks.append(track)
	looper.add(track)

def track_next():
	global track
	if track+1<len(tracks): track+=1

def track_prev():
	global track
	if track.get()>0: track-=1

def uncrop():
	looper.commander.queue_command(
		looper.commander,
		'period',
		0,
		edges_to_wait=edges_to_wait
	)

def wait_more():
	global edges_to_wait
	edges_to_wait+=1

def wait_less():
	global edges_to_wait
	if edges_to_wait.get()>0: edges_to_wait-=1

def generate_standard_command(function, sense):
	def command(): function(looper, tracks[track], sense, edges_to_wait)
	return command

commands={
	'Return': lambda: looper.reset(),
	'Space': lambda: looper.crop(),
	'\\': uncrop,
	'U': track_next,
	'J': track_prev,
	'I': wait_more,
	'K': wait_less,
	'1': command_add_midi,
	'Q': generate_standard_command(dlal.Looper.record, False),
	'A': generate_standard_command(dlal.Looper.record, True),
	'W': generate_standard_command(dlal.Looper.play  , False),
	'S': generate_standard_command(dlal.Looper.play  , True),
	'E': generate_standard_command(dlal.Looper.replay, False),
	'D': generate_standard_command(dlal.Looper.replay, True),
}

def command(text):
	c=text.decode('utf-8').split()
	name=c[0]
	sense=int(c[1])
	if sense: commands[name]()
for name in commands: looper.commander.register_command(name, command)

#start
looper.audio.start()
atexit.register(lambda: looper.audio.finish())
