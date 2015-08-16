import dlal, atexit

#create
system=dlal.System()
network=dlal.Component('network')
commander=dlal.Commander()
midi=dlal.Component('midi')
fm=dlal.Fm()
audio=dlal.Component('audio')
#command
audio.set(44100, 6)
#add
system.add(audio, network, commander, midi, fm)
#connect
network.connect(commander)
commander.connect(midi)
midi.connect(fm)
fm.connect(audio)
#start
fm.show_controls()

#notes
octave=5

def octavate(o):
	global octave
	octave+=o

commands={
	'Z':  0, 'S':  1, 'X':  2, 'D':  3, 'C':  4, 'V':  5,
	'G':  6, 'B':  7, 'H':  8, 'N':  9, 'J': 10, 'M': 11,
	',': 12, 'L': 13, '.': 14, ';': 15, '/': 16,
	'Q': 11,
	'W': 12, '3': 13, 'E': 14, '4': 15, 'R': 16, 'T': 17,
	'6': 18, 'Y': 19, '7': 20, 'U': 21, '8': 22, 'I': 23,
	'O': 24, '0': 25, 'P': 26, '-': 27, '[': 28
}

def command(text):
	c=text.decode('utf-8').split()
	name=c[0]
	sense=int(c[1])
	status=[0x80, 0x90][sense]
	if   name=='PageUp'  : sense and octavate(+1)
	elif name=='PageDown': sense and octavate(-1)
	else: commander.queue(0, 0, 'midi', status, octave*12+commands[name], 0x40)

commander.register_command('PageUp'  , command)
commander.register_command('PageDown', command)
for name in commands: commander.register_command(name, command)

#main
def go(port=None):
	atexit.register(lambda: audio.finish())
	audio.start()
	if port: midi.open(port)

print('available midi ports:\n', midi.ports())
print('use the go function to start audio processing')
