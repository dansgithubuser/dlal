#liner

import dlal

log_2_samples_per_evaluation=6

#create
system=dlal.System()
raw=dlal.Component('raw')
liner=dlal.Liner(16<<log_2_samples_per_evaluation, 16<<log_2_samples_per_evaluation)
sonic_controller=dlal.SonicController()
#command
raw.set(44100, log_2_samples_per_evaluation)
liner.line('z')
#add
system.add(raw, slot=1)
system.add(liner, sonic_controller)
#connect
liner.connect(sonic_controller)
sonic_controller.connect(raw)
#start
raw.start()
