'A vocoder built around vocoder component.'

import dlal

import dansplotcore as dpc

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('input_path')
parser.add_argument('--peak-smooth-rise', type=float)
parser.add_argument('--peak-smooth-fall', type=float)
parser.add_argument('--gain-smooth-rise', type=float)
parser.add_argument('--gain-smooth-fall', type=float)
parser.add_argument('--gain-min', type=float)
parser.add_argument('--gain-max', type=float)
args = parser.parse_args()

audio = dlal.Audio(driver=True)
afr = dlal.Afr(args.input_path)
compressor = dlal.Compressor()
buf = dlal.Buf()
tape = dlal.Tape()

if args.peak_smooth_rise:
    compressor.peak_smooth_rise(args.peak_smooth_rise)
if args.peak_smooth_fall:
    compressor.peak_smooth_fall(args.peak_smooth_fall)
if args.gain_smooth_rise:
    compressor.gain_smooth_rise(args.gain_smooth_rise)
if args.gain_smooth_fall:
    compressor.gain_smooth_fall(args.gain_smooth_fall)
if args.gain_min:
    compressor.gain_min(args.gain_min)
if args.gain_max:
    compressor.gain_max(args.gain_max)

dlal.connect(
    afr,
    [buf, '<+', compressor],
    tape,
)

data = []

duration = afr.duration()
file = open('out.i16le', 'wb')
while afr.playing():
    audio.run()
    tape.to_file_i16le(file)
    elapsed = afr.elapsed()
    print(f'{elapsed:9.3f} s', end='\r')
    data.append((
        elapsed,
        1/compressor.gain(),
        compressor.peak_smoothed(),
        compressor.peak(),
    ))
print()
file.close()
dlal.sound.i16le_to_flac('out.i16le')

plot = dpc.Plot(primitive=dpc.p.Line())
for c in range(1, len(data[0])):
    plot.plot([(i[0], i[c]) for i in data])
plot.show()
