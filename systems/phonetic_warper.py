import dlal

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('audio_path')
args = parser.parse_args()

frames = dlal.speech.file_to_frames(args.audio_path)
split = dlal.speech.split_frames(frames)

audio = dlal.Audio()
run_size = audio.run_size()
sample_rate = audio.sample_rate()
t = 0
for frames in split:
    t += len(frames) * run_size / sample_rate
    print(f'{t:>8.3f}')
