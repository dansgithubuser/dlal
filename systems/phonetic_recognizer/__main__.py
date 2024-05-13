def timestamp():
    import datetime
    return '{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.datetime.now())

print('===== Setup =====')
print(timestamp())

import dlal

import cmudict
import whisper

import argparse
import glob
import math
import os
from pathlib import Path
import pprint
import re
import sys

parser = argparse.ArgumentParser()
parser.add_argument('audio_glob')
parser.add_argument(
    '--model',
    '-m',
    choices=['tiny', 'base', 'small', 'medium', 'large'],
    default='base',
)
parser.add_argument('--output-aligner-dataset', '--oad',
    type=Path,
    nargs='?',
    const=Path('.'),
    metavar='path',
    help='default .',
)
args = parser.parse_args()

def split(sound):
    return sound.split(window_backward=sound.sample_rate * 10)

print('===== Load Model =====')
print(timestamp())
try:
    model = whisper.load_model(args.model)
except Exception as e:
    if type(e).__name__ != 'OutOfMemoryError':
        raise
    if os.environ.get('CUDA_VISIBLE_DEVICES') == '':
        raise
    print("Ran out of VRAM. Try CUDA_VISIBLE_DEVICES=''")
    sys.exit(1)

for audio_path in sorted(glob.glob(args.audio_glob)):
    print(f'===== Transcribe {audio_path} =====')
    print(timestamp())
    tmp_path = 'phonetic_recognizer_tmp.flac'
    transcriptions = []
    sound = dlal.sound.read(audio_path)
    for sound_part in split(sound):
        sound_part.to_flac(tmp_path)
        transcription = model.transcribe(
            tmp_path,
            verbose=True,
            word_timestamps=True,
            language='en',
        )
        transcription['start_time'] = sound_part.start_time
        transcriptions.append(transcription)
    os.remove(tmp_path)

    print(f'===== Results {audio_path} =====')
    print(timestamp())
    for transcription in transcriptions:
        print(f'transcription starting at {transcription["start_time"]:.3f}')
        print(transcription['text'])
        for segment in transcription['segments']:
            for word in segment['words']:
                ipa = cmudict.convert(re.sub('[ ,.?]', '', word['word']))
                print(f'''{word['start']:5.2f} {word['end']:5.2f}''', word['word'], ipa)
        print()

    if args.output_aligner_dataset:
        sound = dlal.sound.read(audio_path)
        for sound_part, transcription in zip(split(sound), transcriptions):
            out_dir = args.output_aligner_dataset / f'recognized-{audio_path.stem}' / '{sound_part.start_time:08.3f}'
            out_dir.mkdir(parents=True, exist_ok=True)
            size = sum(len(segment['words']) for segment in transcription['segments'])
            size_mag = math.floor(math.log10(size)) + 1
            index_fmt = f'{{:0{size_mag}}}'
            for segment_i, segment in enumerate(transcription['segments']):
                prefix = out_dir / index_fmt.format(segment_i + 1)
                sound.copy(segment['start'], segment['end']).to_flac(prefix.with_suffix('.flac'))
                with open(prefix.with_suffix('.txt'), 'w') as txt:
                    txt.write(segment['text'].strip().upper())
