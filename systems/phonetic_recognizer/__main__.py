def timestamp():
    import datetime
    return '{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.datetime.now())

print('===== Setup =====')
print(timestamp())

import dlal

import cmudict
import whisper

import argparse
import math
import os
from pathlib import Path
import pprint
import re
import sys

parser = argparse.ArgumentParser()
parser.add_argument('audio_path', type=Path)
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

print('===== Transcribe =====')
print(timestamp())
result = model.transcribe(
    str(args.audio_path),
    verbose=True,
    word_timestamps=True,
    language='en',
)

print('===== Results =====')
print(timestamp())
print('----- Whisper Output -----')
pprint.pprint(result)
print('----- IPA -----')
for segment in result['segments']:
    for word in segment['words']:
        ipa = cmudict.convert(re.sub('[ ,.?]', '', word['word']))
        print(f'''{word['start']:5.2f} {word['end']:5.2f}''', word['word'], ipa)

if args.output_aligner_dataset:
    sound = dlal.sound.read(args.audio_path)
    out_dir = args.output_aligner_dataset / ('recognized-' + args.audio_path.stem)
    out_dir.mkdir(parents=True, exist_ok=True)
    size = sum(len(segment['words']) for segment in result['segments'])
    size_mag = math.floor(math.log10(size)) + 1
    index_fmt = f'{{:0{size_mag}}}'
    for segment_i, segment in enumerate(result['segments']):
        prefix = out_dir / index_fmt.format(segment_i + 1)
        sound.copy(segment['start'], segment['end']).to_flac(prefix.with_suffix('.flac'))
        with open(prefix.with_suffix('.txt'), 'w') as txt:
            txt.write(segment['text'].strip().upper())
