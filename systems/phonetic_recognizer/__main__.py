def timestamp():
    import datetime
    return '{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.datetime.now())

print('===== Setup =====')
print(timestamp())
import cmudict

import whisper

import argparse
import os
import pprint
import re
import sys

parser = argparse.ArgumentParser()
parser.add_argument('audio_path')
parser.add_argument(
    '--model',
    '-m',
    choices=['tiny', 'base', 'small', 'medium', 'large'],
    default='base',
)
args = parser.parse_args()

print('===== Load Model =====')
print(timestamp())
try:
    model = whisper.load_model(args.model)
except:
    if type(e).__name__ != 'OutOfMemoryError':
        raise
    if os.environ.get('CUDA_VISIBLE_DEVICES') == '':
        raise
    print("Ran out of VRAM. Try CUDA_VISIBLE_DEVICES=''")
    sys.exit(1)

print('===== Transcribe =====')
print(timestamp())
result = model.transcribe(
    args.audio_path,
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
        print(word['start'], word['end'], word['word'], ipa)
