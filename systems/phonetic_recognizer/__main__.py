import whisper

import argparse
import pprint

parser = argparse.ArgumentParser()
parser.add_argument('audio_path')
args = parser.parse_args()

model = whisper.load_model('base')
result = model.transcribe(
    args.audio_path,
    verbose=True,
    word_timestamps=True,
)
pprint.pprint(result)
