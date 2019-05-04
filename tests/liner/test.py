#liner

import dlal

log_2_samples_per_evaluation=6

#create
system=dlal.System()
raw=dlal.Component('raw')
liner=dlal.Liner(16<<log_2_samples_per_evaluation, 16<<log_2_samples_per_evaluation)
sonic_controller=dlal.SonicController()
#command
raw.set(44100, log_2_samples_per_evaluation, immediate=True)
liner.line('z', immediate=True)
#add
system.add(raw, slot=1, immediate=True)
system.add(liner, sonic_controller, immediate=True)
#connect
liner.connect(sonic_controller, immediate=True)
sonic_controller.connect(raw, immediate=True)
#start
raw.start(immediate=True)
