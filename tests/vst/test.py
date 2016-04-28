import dlal, os, platform, sys

#create
system=dlal.System()
raw=dlal.Component('raw')
midi=dlal.Component('midi')
vst=dlal.Component('vst')
#command
raw.set(44100, 6)
midi.midi(0x90, 0x3C, 0x40)
#add
system.add(raw, slot=1)
system.add(midi, vst)
#connect
midi.connect(vst)
vst.connect(raw)
#start
file_path=os.path.split(os.path.realpath(__file__))[0]
vst_folder=os.path.join(file_path, '..', '..', 'components', 'vst', 'deps', 'tunefish-v4.0.1')
if   platform.system()=='Windows':
	if sys.maxsize>2**32:
		vst_file='tunefish4-64.dll'
	else:
		vst_file='tunefish4-32.dll'
elif platform.system()=='Darwin':
	vst_file  ='tunefish4.vst'
elif platform.system()=='Linux':
	if sys.maxsize>2**32:
		vst_file='tunefish4-64.so'
	else:
		vst_file='tunefish4-32.so'
vst.load(os.path.join(vst_folder, vst_file))
#Travis and AppVeyor don't have screens or something...
#vst.show_test(100, os.path.join(file_path, 'expected.png'))
raw.start()
