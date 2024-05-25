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

for midi_phrase, audio_path in zip(midi_split, audio_paths):
    audio_frames = dlal.speech.file_to_frames(audio_path, quiet=True)
    t_t = sum(i.delta for i in midi_phrase[1:])
    t = 0
    audio_frameses = []
    for deltamsg in midi_phrase[1:]:
        a_i = int(t / t_t * len(audio_frames))
        t += deltamsg.delta
        a_f = int(t / t_t * len(audio_frames))
        audio_frameses.append(audio_frames[a_i:a_f])
    dlal.speech.Utterance.from_frameses_and_deltamsgs(audio_frameses, midi_phrase)
