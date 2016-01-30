def standard_system_functionality(system, audio, midi=None, extra_help=[]):
	import sys
	def go():
		audio.start()
		print('audio processing going')
	def quit():
		audio.finish()
		system.demolish()
		sys.exit()
	print('use the go function to start audio processing')
	print('use the quit function to quit')
	for help in extra_help: print(help)
	if len(sys.argv)>1 and sys.argv[1]=='-g':
		print('-g option specified -- starting audio processing')
		go()
	if midi:
		ports=[x for x in midi.ports().split('\n') if len(x)]
		if len(ports):
			print('opening midi port '+ports[0])
			midi.open(ports[0])
	return go, quit, ports
