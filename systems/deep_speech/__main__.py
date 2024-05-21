import argparse

parser = argparse.ArgumentParser()
parser.add_argument('text')
parser.add_argument('--speaker', default='assets/phonetics/sample1.flac')
parser.add_argument('--output', '-o', default='output.wav')
args = parser.parse_args()

from TTS.api import TTS

tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2').to('cpu')
tts.tts_to_file(
    text=args.text,
    speaker_wav=args.speaker,
    language='en',
    file_path=args.output,
)
