def standard_system_functionality(audio, midi=None, extra_help=[]):
	import sys, atexit
	def go():
		audio.start()
		atexit.register(lambda: audio.finish())
		print('audio processing going')
	print('use the go function to start audio processing')
	for help in extra_help: print(help)
	if len(sys.argv)>1 and sys.argv[1]=='-g':
		print('-g option specified -- starting audio processing')
		go()
	if midi:
		ports=[x for x in midi.ports().split('\n') if len(x)]
		if len(ports):
			print('opening midi port '+ports[0])
			midi.open(ports[0])
	return go, ports
