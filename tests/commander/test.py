#commander, liner, switch

import dlal

sample_rate=44100
log_2_samples_per_callback=6

#create
system=dlal.System()
liner=dlal.Liner(sample_rate*10, sample_rate)
fm1=dlal.Fm(sample_rate)
fm2=dlal.Fm(sample_rate)
commander=dlal.Commander()
switch1=dlal.Component('switch')
switch1.resize(1<<log_2_samples_per_callback)
switch2=dlal.Component('switch')
switch2.resize(1<<log_2_samples_per_callback)
raw=dlal.Component('raw')
#connect
fm1.connect_input(liner)
fm2.connect_input(liner)
commander.connect_output(switch1)
commander.connect_output(switch2)
fm1.connect_output(switch1)
fm2.connect_output(switch2)
switch1.connect_input(raw)
switch2.connect_input(raw)
#command
liner.line('z')
fm2.o(0, 0.5)
commander.period(2<<log_2_samples_per_callback)
commander.queue(1, 0, 'unset')
commander.queue(1, 1, 'set 0')
commander.queue(2, 0, 'set 0')
commander.queue(2, 1, 'unset')
def commander_callback(text): commander._report(text)
commander.set_callback(commander_callback)
switch1.set(0)
switch2.unset()
raw.set(sample_rate, log_2_samples_per_callback)
#add
liner.add(system)
raw.add(system)
commander.add(system)
switch1.add(system)
switch2.add(system)
fm1.add(system)
fm2.add(system)
#start
raw.start()
