import dlal

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--midi-path', '-m')
args = parser.parse_args()

audio = dlal.Audio(driver=True)
comm = dlal.Comm()
liner = dlal.Liner()
soundfont = dlal.Soundfont()
tape = dlal.Tape()

for i in range(16):
    liner.connect(soundfont)
dlal.connect(
    soundfont,
    [audio, tape],
)

duration = None
if args.midi_path:
    liner.load(args.midi_path, immediate=True)
    duration = liner.duration()

dlal.typical_setup(duration=duration)
