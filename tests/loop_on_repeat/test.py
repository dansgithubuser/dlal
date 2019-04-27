import dlal

log2_samples_per_evaluation=3
samples_per_evaluation=1<<log2_samples_per_evaluation

#create
system=dlal.System()
raw=dlal.Component('raw')
liner=dlal.Liner(period_in_samples=8*samples_per_evaluation)
sonic_controller=dlal.SonicController()
#command
raw.set(44100, log2_samples_per_evaluation)
liner.loop_on_repeat()
liner.set_fudge(0)
sonic_controller.a(1)
sonic_controller.d(1)
sonic_controller.s(1)
sonic_controller.r(1)
#add
system.add(raw, slot=1)
system.add(liner, sonic_controller)
#connect
liner.connect(sonic_controller)
sonic_controller.connect(raw)
#start
raw.start(1)

def note(number, on):
	if on:
		cmd=0x90
	else:
		cmd=0x80
	liner.midi(cmd, number, 0x7f)
	sonic_controller.midi(cmd, number, 0x7f)

for i in range(2):
	note(60, True)
	raw.evaluate()
	note(60, False)
	for i in range(3): raw.evaluate()
	note(61, True)
	raw.evaluate()
	note(61, False)
	for i in range(3): raw.evaluate()

for i in range(8): raw.evaluate()
