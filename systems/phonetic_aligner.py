#===== imports =====#
#----- in-repo -----#
import dlal

#----- deps -----#
import midi

#----- 3rd party -----#
import dansplotcore as dpc

#----- standard -----#
import argparse
import json
import math
from pathlib import Path
import time

#===== args =====#
parser = argparse.ArgumentParser()
parser.add_argument('--midi', '-m', nargs=2, metavar=('path', 'track'))
parser.add_argument('--audio-path', '-a', nargs='+')
args = parser.parse_args()

#===== helpers =====#
def edit(frames, frame_indices, notes):
    plot = dpc.Plot('aligner')
    variables = []
    samples_i = notes[0]['on']
    color = [0.0, 1.0, 1.0]
    for i, frame in enumerate(frames):
        l = len(frame['noise']['spectrum'])
        for k, v in enumerate(frame['noise']['spectrum']):
            plot.rect(
                i,
                (-1 + (k + 0) / l) * 10,
                i + 1,
                (-1 + (k + 1) / l) * 10,
                a=math.log10(1000 * v + 1e-6),
            )
    for i, ((a, b), note) in enumerate(zip(frame_indices, notes)):
        plot.rect(
            (note['on'] - samples_i) / 64,
            note['number'] - 0.5,
            (note['off'] - samples_i) / 64,
            note['number'] + 0.5,
            *color
        )
        variables.append([
            plot.variable(
                f'<{i}',
                a,
                1,
                'x',
                home=((note['on'] - samples_i) / 64, note['number']),
            ),
            plot.variable(
                f'{i}>',
                b,
                0,
                'x',
                home=((note['off'] - samples_i) / 64, note['number']),
            ),
        ])
        color[2] = 1.0 - color[2]
    plot.show()
    return [[int(i()), int(j())] for i, j in variables]

#===== main =====#
midi_path, midi_track = args.midi
liner = dlal.Liner(midi_path)
notes = liner.get_notes(int(midi_track))
noteses = dlal.Liner.split_notes(notes)
audio_paths = sorted(args.audio_path)

assert len(noteses) == len(audio_paths), f'{len(noteses)} {len(audio_paths)}'

audio = dlal.Audio()
speech_synth = dlal.speech.SpeechSynth()
audio.add(speech_synth)
dlal.connect(speech_synth, audio)

for notes, audio_path in zip(noteses, audio_paths):
    output_path = Path(audio_path).with_suffix('.json')
    if output_path.exists(): continue
    samples_i = notes[0]['on']
    samples_f = notes[-1]['off']
    samples_total = samples_f - samples_i
    frames = dlal.speech.file_to_frames(audio_path, quiet=True)
    frame_indices = []
    frameses = []
    frame_f = len(frames) - 1
    while sum(frames[frame_f]['noise']['spectrum']) < 0.001:
        frame_f -= 1
    for i, note in enumerate(notes):
        a = int((note['on'] - samples_i) / samples_total * frame_f)
        if i + 1 < len(notes):
            b = int((notes[i+1]['on'] - samples_i) / samples_total * frame_f)
        else:
            b = int((notes[-1]['off'] - samples_i) / samples_total * frame_f)
        frame_indices.append([a, b])
        frameses.append(frames[a:b])
    utterance = dlal.speech.Utterance.from_frameses_and_notes(frameses, notes)
    while True:
        audio.start()
        speech_synth.utter(utterance)
        time.sleep(samples_total / 44100)
        audio.stop()
        print('Enter to say again, e to edit, n for next phrase, q to quit.')
        i = input()
        if i == 'e':
            frame_indices = edit(frames, frame_indices, notes)
            frameses = [frames[a:b] for a, b in frame_indices]
            utterance = dlal.speech.Utterance.from_frameses_and_notes(frameses, notes)
            continue
        if i == 'n': break
        if i == 'q': break
    if i == 'q': break
    with open(output_path, 'w') as f:
        f.write(json.dumps(frame_indices))
