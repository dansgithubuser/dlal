import argparse
import json
import math
import os

try:
    import dansplotcore as dpc
except:
    pass

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['analyze_model', 'train', 'transcode'], default='train')
parser.add_argument('--recording-path', default='assets/phonetics/sample1.flac')
parser.add_argument('--markov-model-path', default='assets/phonetics/markov-model.json')
parser.add_argument('--plot', action='store_true')
args = parser.parse_args()

os.environ['PHONETIC_ENCODER_RECORDING_PATH'] = args.recording_path
import dlal
import phonetic_encoder as pe
dlal.comm_set(None)
import phonetic_decoder as pd

run_size = pe.audio.run_size()
duration = pe.filea.duration()
samples = 0

if args.plot:
    plot = dpc.Plot()

#===== helpers =====#
def serialize_features(features):
    return ''.join(['{:03x}'.format(math.floor(i * 256)) for i in features])

def bucketize(features):
    if features[0] < 0.3:
        return serialize_features(features[1:5])
    else:
        return serialize_features(features[5:])

#===== actions =====#
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
            features = dlal.speech.get_features(frame)
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
    bucket_prev = None
    while samples < duration:
        print(f'{samples / duration * 100:.1f} %')
        pe.audio.run()
        sample = pe.sample_system()
        params = pe.parameterize(*sample)
        features = dlal.speech.get_features(params)
        bucket = bucketize(features)
        if bucket not in mmodel:
            print(f'create bucket {bucket}')
            mmodel[bucket] = {
                'params': params,
                'nexts': {},
            }
        if bucket_prev:
            nexts_prev = mmodel[bucket_prev]['nexts']
            nexts_prev.setdefault(bucket, 0)
            nexts_prev[bucket] += 1
        if args.plot:
            plot.point(samples, len(mmodel))
        bucket_prev = bucket
        samples += run_size
    with open(args.markov_model_path, 'w') as f:
        f.write(json.dumps(mmodel))

def transcode():
    global samples
    file = open('phonetic_markov.i16le', 'wb')
    with open(args.markov_model_path) as f:
        mmodel = json.loads(f.read())
    while samples < duration:
        print(f'{samples / duration * 100:.1f} %')
        pe.audio.run()
        sample = pe.sample_system()
        params = pe.parameterize(*sample)
        features = dlal.speech.get_features(params)
        bucket = bucketize(features)
        if bucket in mmodel:
            transams = mmodel[bucket]
        else:
            print(f'missing bucket {bucket}')
            d_min = math.inf
            for k, v in mmodel.items():
                d = dlal.speech.params_distance(params, v)
                if d < d_min:
                    transams = v
                    d_min = d
        frame = pe.frames_from_params([transams])[0]
        pd.synth.synthesize(
            [i[0] for i in frame['tone']['spectrum']],
            [i[0] for i in frame['noise']['spectrum']],
            0,
        )
        pd.audio.run()
        pd.tape.to_file_i16le(file)
        samples += run_size

#===== main =====#
eval(args.action)()
if args.plot: plot.show()
