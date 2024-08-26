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

pole_pairs = [
    (1000, 0.02),
    (1500, 0.03), 
    (2500, 0.03), 
    (3000, 0.03), 
    (3500, 0.03), 
    (4000, 0.03), 
    (5000, 0.03), 
    (6000, 0.03), 
    (7000, 0.03), 
    (8000, 0.03), 
    (2000, 0.03), 
]
for freq, width in pole_pairs:
    iir.pole_pairs_bandpass(freq / audio.sample_rate(), width, add=True)

dlal.connect(
    afr,
    [buf, '<+', iir],
    [audio, tape],
)

dlal.typical_setup(duration=afr.duration() / audio.sample_rate())
