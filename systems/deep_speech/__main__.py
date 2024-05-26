import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--text')
parser.add_argument('--convert', help='path to audio file to convert to speaker voice')
parser.add_argument('--speaker', default='assets/phonetics/sample1.flac', help='sample of speaker voice')
parser.add_argument('--output', '-o', default='output.wav')
args = parser.parse_args()

from TTS.api import TTS

if args.text:
    tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2').to('cpu')
    tts.tts_to_file(
        text=args.text,
        speaker_wav=args.speaker,
        language='en',
        file_path=args.output,
    )

if args.convert:
    tts = TTS('voice_conversion_models/multilingual/vctk/freevc24').to('cpu')
    tts.voice_conversion_to_file(
        source_wav=args.convert,
        target_wav=args.speaker,
        file_path=args.output,
    )
