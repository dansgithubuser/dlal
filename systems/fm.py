import dlal, atexit

sample_rate=44100

#create
system=dlal.System()
sfml=dlal.Component('sfml')
fm=dlal.Fm(sample_rate)
audio=dlal.Component('audio')
#connect
fm.connect_input(sfml)
fm.connect_output(audio)
#command
log_2_samples_per_callback=6
audio.command('set {0} {1}'.format(sample_rate, log_2_samples_per_callback))
#add
sfml.add(system)
audio.add(system)
fm.add(system)
#start
atexit.register(lambda: audio.command('finish'))
fm.show_controls()
try:
	vgm=fm.get_vgm('vgm', 485100)
	fm.set_vgm(vgm, 1)
except Exception as e: print(e)

def go(): audio.command('start')
