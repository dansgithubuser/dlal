import dlal, os, subprocess

#create
system=dlal.System()
raw=dlal.Component('raw')
qweboard=dlal.Qweboard()
midi=dlal.Component('midi')
fm=dlal.Fm()
#command
raw.set(44100, 6)
#add
system.add(raw, slot=1)
system.add(qweboard, midi, fm)
#connect
qweboard.connect(midi)
midi.connect(fm)
fm.connect(raw)
#network client
os.environ['PATH']='.'
subprocess.check_call('Softboard 127.0.0.1 9120 "Z 1"', shell=True)
#start
raw.start()
