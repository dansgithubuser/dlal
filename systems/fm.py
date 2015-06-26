import dlal, atexit

sample_rate=44100

#create
system=dlal.System()
network=dlal.Component('network')
fm=dlal.Fm(sample_rate)
audio=dlal.Component('audio')
midi=dlal.Component('midi')
switch=dlal.Component('switch')
#connect
switch.connect_input(network)
switch.connect_input(midi)
fm.connect_input(switch)
fm.connect_output(audio)
#command
log_2_samples_per_callback=6
audio.set(sample_rate, log_2_samples_per_callback)
switch.set(0)
#add
network.add(system)
midi.add(system)
audio.add(system)
fm.add(system)
#start
fm.show_controls()

def go(port=''):
	atexit.register(lambda: audio.finish())
	audio.start()
	if type(port)==str:
		midi.open(port)
		switch.set(1)
	else:
		network.open(9089)

print('available midi ports:\n', midi.ports())
print('use the go function to start audio processing')
