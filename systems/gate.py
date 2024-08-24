'A vocoder built around vocoder component.'

import dlal

import dansplotcore as dpc

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('input_path')
parser.add_argument('threshold', type=float)
args = parser.parse_args()

audio = dlal.Audio(driver=True)
afr = dlal.Afr(args.input_path)
peak = dlal.Peak()
buf1 = dlal.Buf()
gate = dlal.Gate()
buf2 = dlal.Buf()
tape = dlal.Tape()

gate.threshold(args.threshold)

dlal.connect(
    afr,
    [buf1, '+>', peak],
    [buf2, '<+', gate],
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
        gate.gain(),
        peak.value(),
    ))
print()
file.close()
dlal.sound.i16le_to_flac('out.i16le')

plot = dpc.Plot(primitive=dpc.p.Line())
for c in range(1, len(data[0])):
    plot.plot([(i[0], i[c]) for i in data])
plot.show()
