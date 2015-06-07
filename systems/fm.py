import dlal, atexit

sample_rate=44100

#create
system=dlal.System()
sfml=dlal.Component('sfml')
fm=dlal.Fm(sample_rate)
audio=dlal.Component('audio')
midi=dlal.Component('midi')
switch=dlal.Component('switch')
#connect
switch.connect_input(sfml)
switch.connect_input(midi)
fm.connect_input(switch)
fm.connect_output(audio)
#command
log_2_samples_per_callback=6
audio.command('set {0} {1}'.format(sample_rate, log_2_samples_per_callback))
switch.command('set 0')
#add
sfml.add(system)
midi.add(system)
audio.add(system)
fm.add(system)
#start
fm.show_controls()

def go(port=''):
	atexit.register(lambda: audio.command('finish'))
	audio.command('start')
	if port:
		midi.command('open '+port)
		switch.command('set 1')

print('available midi ports:\n', midi.command('ports'))
print('use the go function to start audio processing')
