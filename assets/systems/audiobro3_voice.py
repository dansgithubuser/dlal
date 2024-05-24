import dlal

import os

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
    for i, line in enumerate(text.splitlines()):
        deep_speech_path = f'assets/local/audiobro3_deep_speech_{i:02}.wav'
        if not os.path.exists(deep_speech_path):
            if not tts:
                from TTS.api import TTS
                tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2').to('cpu')
            tts.tts_to_file(
                text=line,
                speaker='Aaron Dreschner',
                language='en',
                file_path=deep_speech_path,
            )
    print('All good? Enter q to quit. Otherwise delete files and enter to redo those.')
    if input() == 'q':
        break
