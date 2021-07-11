import argparse
import json
import math
import os

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['analyze_model', 'train'], default='train')
parser.add_argument('--normalize', action='store_true')
parser.add_argument('--recording-path', default='assets/phonetics/sample1.flac')
args = parser.parse_args()

os.environ['PHONETIC_ENCODER_RECORDING_PATH'] = args.recording_path
import dlal
import phonetic_encoder as pe

run_size = pe.audio.run_size()
duration = pe.filea.duration()
samples = 0

def analyze_model():
    with open('assets/phonetics/model.json') as f:
        model = json.loads(f.read())
    ranges = {}
    for phonetic, info in model.items():
        for frame in info['frames']:
            group = (info['type'], info['voiced'], info['fricative'])
            ranges.setdefault(group, [
                [+math.inf for i in range(7)],
                [-math.inf for i in range(7)],
            ])
            features = dlal.speech.get_features(frame, normalized=args.normalize)
            ranges[group][0] = [min(i, j) for i, j in zip(features, ranges[group][0])]
            ranges[group][1] = [max(i, j) for i, j in zip(features, ranges[group][1])]
    for group, group_ranges in sorted(ranges.items()):
        print('voiced' if group[1] else 'unvoiced', 'fricative' if group[2] else 'nonfricative', group[0])
        for i, name in enumerate(['toniness', 'f1', 'f2', 'f2_amp', 'f3_amp', 'fn', 'hi']):
            print(f'\t{name:>8} {group_ranges[0][i]:>8.3f} {group_ranges[1][i]:>8.3f}')

def train():
    while samples < duration:
        pe.audio.run()
        sample = pe.sample_system()
        params = pe.parameterize(*sample)

eval(args.action)()
