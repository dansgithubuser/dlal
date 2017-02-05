import dlal, os, sys

input_buffer=dlal.Buffer()
peak=dlal.Component('peak')
multiplier=dlal.Component('multiplier')
peak_buffer=dlal.Buffer()
output_buffer=dlal.Buffer()

input_buffer.connect(peak_buffer)
input_buffer.connect(output_buffer)
peak.connect(peak_buffer)
multiplier.connect(peak_buffer)
multiplier.connect(output_buffer)

dlal.SimpleSystem.sample_rate=8000
system=dlal.SimpleSystem(
	[input_buffer, peak, multiplier, peak_buffer, output_buffer],
	outputs=[],
	test=True,
)

input_buffer.load_sound(0x3c, os.environ['DLAL_COMPRESS_INPUT'])
samples=dlal.helpers.round_up(int(input_buffer.sound_samples(0x3c)), system.samples_per_evaluation)
peak.invert_coefficient(1)
peak.coefficient(0)
peak_buffer.clear_on_evaluate('y')
output_buffer.periodic_resize(samples)
system.audio.duration(1000.0*samples/system.sample_rate)

go, ports=system.standard_system_functionality()
x=os.environ['DLAL_COMPRESS_INPUT'].split('.')
x[-1]='out.'+x[-1]
output_buffer.save('.'.join(x))

class Q:
	def __repr__(self): sys.exit()

q=Q()
