import dlal, os, sys

input_file_path=os.environ['DLAL_COMPRESS_INPUT']

input_filea=dlal.Component('filea')
peak=dlal.Component('peak')
multiplier=dlal.Component('multiplier')
peak_buffer=dlal.Buffer()
output_buffer=dlal.Buffer()
output_filea=dlal.Component('filea')

input_filea.connect(peak_buffer)
input_filea.connect(output_buffer)
peak.connect(peak_buffer)
multiplier.connect(peak_buffer)
multiplier.connect(output_buffer)
output_buffer.connect(output_filea)

dlal.SimpleSystem.sample_rate=8000
dlal.SimpleSystem.log_2_samples_per_evaluation=12
system=dlal.SimpleSystem(
	[input_filea, peak, multiplier, peak_buffer, output_filea, output_buffer],
	midi_receivers=[],
	outputs=[],
	raw=True,
)

input_filea.open_read(input_file_path)
peak.invert_coefficient(1)
peak.coefficient(0)
peak_buffer.clear_on_evaluate('y')
output_buffer.clear_on_evaluate('y')
x=input_file_path.split('.')
x[-1]='out.'+x[-1]
output_filea.open_write('.'.join(x))
system.audio.duration(1000.0*int(input_filea.samples())/int(input_filea.sample_rate()))
system.audio.set_print('y')
system.audio.do_file('n')

go, ports=system.standard_system_functionality()
output_filea.close_write()

class Q:
	def __repr__(self): sys.exit()

q=Q()
