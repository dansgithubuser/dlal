'A vocoder built around vocoder component.'

import dlal

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('carrier_path', help='The sound to be vocoded. Usually a rich sound.')
parser.add_argument('modulator_path', help='A sound whose spectrogram will be used to filter the carrier. Usually speech.')
args = parser.parse_args()

audio = dlal.Audio(driver=True)
carrier = dlal.Afr(args.carrier_path)
modulator = dlal.Afr(args.modulator_path)
vocoder = dlal.Vocoder()
buf = dlal.Buf()
tape = dlal.Tape()

dlal.connect(
    carrier,
    [buf, '<+', vocoder, modulator],
    tape,
)

duration = carrier.duration()
file = open('out.i16le', 'wb')
while carrier.playing():
    audio.run()
    tape.to_file_i16le(file)
    print(f'{carrier.elapsed():9.3f} s', end=' ')
    for amp in vocoder.read_band_amps():
        print(f'{amp:6.2f}', end=' ')
    print()
file.close()
dlal.sound.i16le_to_flac('out.i16le')
