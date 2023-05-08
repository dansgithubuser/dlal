print('===== Setup =====')
import cmudict

import whisper

import argparse
import pprint
import re

parser = argparse.ArgumentParser()
parser.add_argument('audio_path')
args = parser.parse_args()

print('===== Load Model =====')
model = whisper.load_model('base')

print('===== Transcribe =====')
result = model.transcribe(
    args.audio_path,
    verbose=True,
    word_timestamps=True,
    language='en',
)

print('===== Results =====')
print('----- Whisper Output -----')
pprint.pprint(result)
print('----- IPA -----')
for segment in result['segments']:
    for word in segment['words']:
        ipa = cmudict.convert(re.sub('[ ,.?]', '', word['word']))
        print(word['start'], word['end'], word['word'], ipa)
