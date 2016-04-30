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

def raw_to_unsigned_8_bit_pcm(input_file_name, output_file_name):
	with open(input_file_name) as file: samples=file.read().split()
	with open(output_file_name, 'wb') as file:
		for sample in samples: file.write(chr(int((float(sample)+1)*63)).encode())
