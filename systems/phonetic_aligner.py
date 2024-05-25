import dlal

import midi

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--midi', '-m', nargs=2, metavar=('path', 'track'))
parser.add_argument('--audio-path', '-a', nargs='+')
args = parser.parse_args()

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
    samples_i = notes[0]['on']
    samples_f = notes[-1]['off']
    samples_total = samples_f - samples_i
    frames = dlal.speech.file_to_frames(audio_path, quiet=True)
    frameses = []
    for i, note in enumerate(notes):
        a = int((note['on'] - samples_i) / samples_total * len(frames))
        if i + 1 < len(notes):
            b = int((notes[i+1]['on'] - samples_i) / samples_total * len(frames))
        else:
            b = int((notes[-1]['off'] - samples_i) / samples_total * len(frames))
        frameses.append(frames[a:b])
    utterance = dlal.speech.Utterance.from_frameses_and_notes(frameses, notes)
    audio.start()
    while True:
        speech_synth.utter(utterance)
        print('Enter to go again, n for next phrase, q to quit.')
        i = input()
        if i == 'n': break
        if i == 'q': break
    audio.stop()
    if i == 'q': break
