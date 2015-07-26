import dlal, atexit

#looper
looper=dlal.Looper()
looper.commander.period(64000*8)
def print_report(text):
	r=dlal.report(text)
	if len(r): print(r)
looper.commander.set_callback(print_report)

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
	track=dlal.MidiTrack(midi, dlal.Fm(), 64000*8, 32000)
	global tracks
	tracks.append(track)
	looper.add(track)

def command_reset():
	looper.reset()

def command_crop():
	looper.crop()

def generate_standard_command(function, sense):
	def command(): function(looper, tracks[0], sense, 0)
	return command

commands={
	'Return': command_reset,
	'Space': command_crop,
	'1': command_add_midi,
	'Q': generate_standard_command(dlal.Looper.record, False),
	'W': generate_standard_command(dlal.Looper.record, True),
	'A': generate_standard_command(dlal.Looper.play  , False),
	'S': generate_standard_command(dlal.Looper.play  , True),
	'Z': generate_standard_command(dlal.Looper.replay, False),
	'X': generate_standard_command(dlal.Looper.replay, True),
}

def command(text):
	c=text.decode('utf-8').split()
	name=c[0]
	sense=int(c[1])
	if sense: commands[name]()
for name in commands: looper.commander.register_command(name, command)

looper.audio.start()
atexit.register(lambda: looper.audio.finish())
