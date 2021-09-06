import argparse
import collections
import json
import math
import os
import random

try:
    import dansplotcore as dpc
except:
    pass

parser = argparse.ArgumentParser(
    description='''
        A phonetic model. It is built atop phonetic_encoder and phonetic_decoder, but works with an independent set of files.

        Whereas a phonetic_encoder model deals with full params, a phonetic_markov model deals with reduced params, or features.

        The following actions can be performed:
        - analyze_model: print out the feature ranges for each phonetic group of a phonetic_encoder model
        - train: start or update a phonetic_markov model
        - transcode: transcode a recording with a phonetic_markov model
        - markovize: take an unmarkovized phonetic_markov model, calculate paths to different phonetics from each bucket, yielding a proper phonetic_markov model

        Example flow:
        `rm assets/phonetics/markov-model.json`
        `./do.py -r 'systems/phonetic_markov.py train --recording-path assets/phonetics/phonetics.flac --labeled'`
        `./do.py -r 'systems/phonetic_markov.py train --recording-path assets/phonetics/sample1.flac'`
        `./do.py -r 'systems/phonetic_markov.py transcode --recording-path something-you-recorded.flac'`
        `./do.py -r 'systems/phonetic_markov.py markovize'`
        `./do.py -r 'systems/phonetic_markov.py generate'`
    ''',
    formatter_class=argparse.RawTextHelpFormatter,
)
parser.add_argument(
    'action',
    choices=[
        'analyze_model',
        'train',
        'transcode',
        'generate_naive',
        'markovize',
        'generate',
        'inspect',
    ],
)
parser.add_argument('--recording-path', default='assets/phonetics/sample1.flac', help='input')
parser.add_argument('--labeled', action='store_true', help='whether the recording was created by phonetic_recorder or not')
parser.add_argument('--markov-model-path', default='assets/phonetics/markov-model.json')
parser.add_argument('--plot', action='store_true')
args = parser.parse_args()

os.environ['PHONETIC_ENCODER_RECORDING_PATH'] = args.recording_path
import dlal
import phonetic_encoder as pe
dlal.comm_set(None)
import phonetic_decoder as pd

PHONETICS = [
    'ae', 'ay', 'a', 'e', 'y', 'i', 'o', 'w', 'uu', 'u',
    'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z', 'm', 'n', 'ng', 'r', 'l',
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]
STOPS = [
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]

phonetics_ashes = [
    'ae', 'sh', 'i', 'z', '0',
    'f', 'a', 'l', '0',
    'th', 'r', 'w', '0',
    'th_v', 'u', '0',
    'm', 'y', 'n', 'y', 'ng', '0',
]
phonetics_sister = [
    'sh', 'y', '0',
    'i', 'z', '0',
    'n', 'a', 't', '0',
    'm', 'ae', 'y', '0',
    's', 'i', 's', 't', 'r', '0',
]

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

def render(vs):
    with open('phonetic_markov.i16le', 'wb') as file:
        for v in vs:
            params = v['params']
            pd.synth.synthesize(
                params['tone']['spectrum'],
                params['noise']['spectrum'],
                0,
            )
            pd.audio.run()
            pd.tape.to_file_i16le(file)

def features_to_frame(features, mmodel):
    bucket = bucketize(features)
    if bucket in mmodel:
        transams = mmodel[bucket]['params']
    else:
        print(f'missing bucket {bucket}')
        d_min = math.inf
        for k, v in mmodel.items():
            d = dlal.speech.features_distance(features, dlal.speech.get_features(v['params']))
            if d < d_min:
                transams = v['params']
                d_min = d
    return pe.frames_from_params([transams])[0]

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
                'phonetics': {},
            }
        if args.labeled:
            seconds = int(samples / 44100)
            deciseconds = int(samples / 4410)
            skip = False
            if seconds % 10 < 3:
                new = True
                if sum(params['tone']['spectrum']) + sum(params['noise']['spectrum']) < 1.5:
                    phonetic = '0'
                else:
                    skip = True
            elif 3 <= seconds % 10 < 9:
                phonetic = PHONETICS[seconds // 10]
                if phonetic in STOPS:
                    spectrum = sample[0]
                    if new and 90 - deciseconds % 100 < 2:
                        skip = True
                    else:
                        s = sum(spectrum[:len(spectrum) // 2])
                        if new:
                            if s < 0.2:
                                skip = True
                        else:
                            if s < 0.01:
                                new = True
                                skip = True
            if not skip:
                phonetics = mmodel[bucket]['phonetics']
                phonetics.setdefault(phonetic, 0)
                phonetics[phonetic] += 1
                new = False
        if bucket_prev:
            nexts_prev = mmodel[bucket_prev]['nexts']
            nexts_prev.setdefault(bucket, 0)
            nexts_prev[bucket] += 1
        if args.plot:
            plot.point(samples, len(mmodel))
        bucket_prev = bucket
        samples += run_size
    with open(args.markov_model_path, 'w') as f:
        f.write(json.dumps(mmodel, indent=2))

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
        frame = features_to_frame(features, mmodel)
        pd.synth.synthesize(
            [i[0] for i in frame['tone']['spectrum']],
            [i[0] for i in frame['noise']['spectrum']],
            0,
        )
        pd.audio.run()
        pd.tape.to_file_i16le(file)
        samples += run_size

def generate_naive(phonetics=phonetics_ashes):
    file = open('phonetic_markov.i16le', 'wb')
    with open('assets/phonetics/model.json') as f:
        model = json.loads(f.read())
    with open(args.markov_model_path) as f:
        mmodel = json.loads(f.read())
    smoother = dlal.speech.Smoother()
    for phonetic in phonetics:
        print(phonetic)
        frame = model[phonetic]['frames'][0]
        for _ in range(200):
            smoothed_frame = smoother.smooth(frame, 0.99)
            features = dlal.speech.get_features(smoothed_frame)
            transframe = features_to_frame(features, mmodel)
            pd.synth.synthesize(
                [i[0] for i in transframe['tone']['spectrum']],
                [i[0] for i in transframe['noise']['spectrum']],
                0,
            )
            pd.audio.run()
            pd.tape.to_file_i16le(file)
    file.close()

def markovize():
    with open(args.markov_model_path) as f:
        mmodel = json.loads(f.read())
    for v in mmodel.values():
        v['next_by_phonetic'] = {}
    prevs = collections.defaultdict(list)
    for k, v in mmodel.items():
        for n in v['nexts']:
            prevs[n].append(k)
    for phonetic in PHONETICS + ['0']:
        print(phonetic)
        visited = set()
        buckets = sorted(mmodel.items(), key=lambda i: -i[1]['phonetics'].get(phonetic, 0))
        buckets = [k for k, v in buckets[:10]]
        # steady-state transitions
        for k in buckets:
            v = mmodel[k]
            next_by_phonetic = v['next_by_phonetic'][phonetic] = {}
            for n, freq_t in v['nexts'].items():
                freq_s = mmodel[n]['phonetics'].get(phonetic, 0)
                if freq_s:
                    next_by_phonetic[n] = freq_t
                    visited.add(k)
        # transient transitions
        queue = buckets
        while queue:
            k = queue[0]
            queue = queue[1:]
            ps = prevs[k]
            for p in ps:
                if p in visited: continue
                mmodel[p]['next_by_phonetic'][phonetic] = {k: 1}
                queue.append(p)
                visited.add(p)
    with open(args.markov_model_path, 'w') as f:
        f.write(json.dumps(mmodel, indent=2))

def generate(phonetics=phonetics_ashes):
    with open(args.markov_model_path) as f:
        mmodel = json.loads(f.read())
    for k, v in mmodel.items():
        if '0' in v['phonetics']:
            break
    file = open('phonetic_markov.i16le', 'wb')
    for phonetic in phonetics:
        print(phonetic)
        for i in range(200):
            v = mmodel[k]
            print(k, v['phonetics'])
            params = v['params']
            pd.synth.synthesize(
                params['tone']['spectrum'],
                params['noise']['spectrum'],
                0,
            )
            pd.audio.run()
            pd.tape.to_file_i16le(file)
            nexts = mmodel[k]['next_by_phonetic'][phonetic]
            k = random.sample(list(nexts.keys()), 1, counts=list(nexts.values()))[0]

def inspect():
    global mmodel
    with open(args.markov_model_path) as f:
        mmodel = json.loads(f.read())

#===== main =====#
eval(args.action)()
if args.plot: plot.show()
