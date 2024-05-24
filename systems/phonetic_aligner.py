import dlal

import midi

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--midi', '-m', nargs=2, metavar=('path', 'track'))
parser.add_argument('--audio-path', '-a', nargs='+')
args = parser.parse_args()

midi_path, midi_track = args.midi
midi_split = midi.Song(midi_path).tracks[int(midi_track)].filter(lambda i: i.is_note()).split()
audio_paths = sorted(args.audio_path)

assert len(midi_split) == len(audio_paths), f'{len(midi_split)} {len(audio_paths)}'
