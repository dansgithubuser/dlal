import dlal

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('input_path', help="A recording to transform so it sounds like it's on the radio.")
args = parser.parse_args()

audio = dlal.Audio(driver=True)
afr = dlal.Afr(args.input_path)
iir = dlal.Iir()
buf = dlal.Buf()
tape = dlal.Tape()

iir.pole_pairs_bandpass(1500 / audio.sample_rate(), 0.02, pairs=1)

dlal.connect(
    afr,
    [buf, '<+', iir],
    [audio, tape],
)

dlal.typical_setup(duration=(afr.duration() / audio.sample_rate() + 1))
