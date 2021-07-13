import argparse
import json
import math
import os

try:
    import dansplotcore as dpc
except:
    pass

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['analyze_model', 'train'], default='train')
parser.add_argument('--normalize', action='store_true')
parser.add_argument('--recording-path', default='assets/phonetics/sample1.flac')
parser.add_argument('--markov-model-path', default='assets/phonetics/markov-model.json')
parser.add_argument('--plot', action='store_true')
args = parser.parse_args()

os.environ['PHONETIC_ENCODER_RECORDING_PATH'] = args.recording_path
import dlal
import phonetic_encoder as pe

run_size = pe.audio.run_size()
duration = pe.filea.duration()
samples = 0

if args.plot:
    plot = dpc.Plot()

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
    global samples
    if os.path.exists(args.markov_model_path):
        with open(args.markov_model_path) as f:
            mmodel = json.loads(f.read())
    else:
        mmodel = {}
    while samples < duration:
        print(f'{samples / duration * 100:.1f} %')
        pe.audio.run()
        sample = pe.sample_system()
        params = pe.parameterize(*sample)
        features = dlal.speech.get_features(params)
        bucket = ''.join(['{:02x}'.format(math.floor((i + 128) * 10)) for i in features])
        if bucket not in mmodel:
            mmodel[bucket] = params
        if args.plot:
            plot.point(samples, len(mmodel))
        samples += run_size
    with open(args.markov_model_path, 'w') as f:
        f.write(json.dumps(mmodel))

eval(args.action)()

if args.plot: plot.show()
