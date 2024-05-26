#===== imports =====#
import dlal

import json
import os
import pickle

#===== deep speech =====#
text = '''\
Oh shit,
it's gettin' serious.
And through smoke, he appeared.
Base man.
The town had been without base for over forty years.
There was no dancing.
There was no rump-shaking.
There had been no laughter.
And death
was nearing
everybody.
We can survive without food,
but not without base.
Well,
not very long anyway.
The color had drained from everyone's faces.
Every day,
the townspeople went to the church and prayed for base.
And base man looked upon the town,
and he smiled,
for he knew.
'''

tts = None
while True:
    something_synthesized = False
    for i, line in enumerate(text.splitlines()):
        deep_speech_path = f'assets/local/audiobro3_deep_speech_{i:02}.wav'
        if not os.path.exists(deep_speech_path):
            print('synthesizing:', line)
            something_synthesized = True
            if not tts:
                from TTS.api import TTS
                tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2').to('cpu')
            tts.tts_to_file(
                text=line,
                speaker='Aaron Dreschner',
                language='en',
                file_path=deep_speech_path,
            )
    if not something_synthesized: break
    print('All good? Enter q to quit. Otherwise delete files and enter to redo those.')
    if input() == 'q': break

#===== alignment =====#
liner = dlal.Liner('assets/midis/audiobro3.mid')
noteses = dlal.Liner.split_notes(liner.get_notes(5))

for i in range(len(text.splitlines())):
    alignment_path = f'assets/local/audiobro3_deep_speech_{i:02}.json'
    if not os.path.exists(alignment_path):
        raise Exception(f'missing {alignment_path}, make it with:\n./do.py -r systems/phonetic_aligner.py -m assets/midis/audiobro3.mid 5 -a assets/local/audiobro3_deep_speech_*.wav')

utterance = dlal.speech.Utterance()
l = len(text.splitlines())
for i in range(l):
    print(f'making utterance {i+1} / {l}')
    with open(f'assets/local/audiobro3_deep_speech_{i:02}.json') as f:
        frame_indices = json.load(f)
    pickle_path = f'assets/local/audiobro3_deep_speech_{i:02}.pickle'
    if os.path.exists(pickle_path):
        with open(pickle_path, 'rb') as f:
            frames = pickle.load(f)
    else:
        frames = dlal.speech.file_to_frames(f'assets/local/audiobro3_deep_speech_{i:02}.wav', quiet=True)
        with open(pickle_path, 'wb') as f:
            pickle.dump(frames, f)
    frameses = [frames[a:b] for a, b in frame_indices]
    u = dlal.speech.Utterance.from_frameses_and_notes(frameses, noteses[i])
    if i == 0:
        t = 0
        pitch = 43
    else:
        t = noteses[i - 1][-1]['off']
        pitch = None
    utterance.append_silence('frame', noteses[i][0]['on'] - t, pitch)
    utterance.extend(u)
utterance.append_silence('frame', 1, None)

#===== render =====#
audio = dlal.Audio(driver=True)
audio.add(liner)
porta = dlal.subsystem.Portamento()
synth = dlal.speech.SpeechSynth()
tape = dlal.Tape(1 << 16)

liner.skip_line(5)
dlal.connect(
    liner,
    porta,
    synth.tone,
    [],
    synth,
    tape,
)

synth.utter(utterance, no_pitch=True)

porta.rhymel.pitch(43 / 128)

# run
runs = int(240 * audio.sample_rate() / audio.run_size())
n = tape.size() // audio.run_size()
with open('assets/local/tmp.i16le', 'wb') as file:
    for i in range(runs):
        audio.run()
        if i % n == n - 1 or i == runs - 1: tape.to_file_i16le(file)
        print(f'{i / runs * 100:>6.2f}%', end='\r')
print()
dlal.sound.i16le_to_flac('assets/local/tmp.i16le', 'assets/local/audiobro3_voice.flac')
