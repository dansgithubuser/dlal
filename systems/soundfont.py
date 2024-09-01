import dlal

import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--midi-path', '-m', type=Path)
parser.add_argument('--gain', '-g', type=float, default=1.0)
parser.add_argument('--ogg', action='store_true')
parser.add_argument('--extra', type=float, default=0.0)
args = parser.parse_args()

audio = dlal.Audio(driver=True)
comm = dlal.Comm()
liner = dlal.Liner()
soundfont = dlal.Soundfont()
gain = dlal.Gain(args.gain)
buf = dlal.Buf()
tape = dlal.Tape()

dlal.connect(
    soundfont,
    [buf, '<+', gain],
    [audio, tape],
)

duration = None
if args.midi_path:
    liner.load(args.midi_path, immediate=True)
    liner.repeat(False)
    duration = liner.duration() + args.extra
    for _ in range(liner.line_count()):
        liner.connect(soundfont)
else:
    liner.connect(soundfont)
flac_path = args.midi_path.with_suffix('.flac')
dlal.typical_setup(
    duration=duration,
    flac_path=flac_path,
)
if args.ogg:
    sound = dlal.sound.read(flac_path)
    sound.to_ogg(args.midi_path.with_suffix('.ogg'))
