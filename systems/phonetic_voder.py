import argparse
import collections
import json
import math
import os
import sqlite3

try:
    import dansplotcore as dpc
except:
    pass

parser = argparse.ArgumentParser(
    description='''
        A phonetic model. It is built atop phonetic_encoder and phonetic_decoder.

        Whereas a phonetic_encoder model deals with full params, a phonetic_voder model deals with reduced params, or features.

        The following actions can be performed:
        - analyze_model: print out the feature ranges for each phonetic group of a phonetic_encoder model
        - train: start or update a phonetic_voder model
        - transcode: transcode a recording with a phonetic_voder model

        Example flow:
        `rm assets/phonetics/voder-model.sqlite3`
        `./do.py -r 'systems/phonetic_voder.py train --recording-path assets/phonetics/phonetics.flac --labeled'`
        `./do.py -r 'systems/phonetic_voder.py train --recording-path assets/phonetics/sample1.flac'`
        `./do.py -r 'systems/phonetic_voder.py transcode --recording-path something-you-recorded.flac'`
        `./do.py -r 'systems/phonetic_voder.py generate'`
    ''',
    formatter_class=argparse.RawTextHelpFormatter,
)
parser.add_argument(
    'action',
    choices=[
        'analyze_model',
        'train',
        'transcode_no_buckets',
        'transcode',
        'generate_naive',
        'generate',
        'interact',
    ],
    nargs='?',
    default='interact',
)
parser.add_argument('--recording-path', default='assets/phonetics/sample1.flac', help='input')
parser.add_argument('--labeled', action='store_true', help='whether the recording was created by phonetic_recorder or not')
parser.add_argument('--voder-model-path', default='assets/phonetics/voder-model.sqlite3')
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
phonetics_fusion = [
    'f', 'y', 'w', 'sh_v', 'i', 'n', '0',
    'h', 'y', 'w', 'm', 'r',
    'i', 'z',
    's', '0', 'o', 'w',
    'm', 'e', '0', 's', '0', 'y', '0',
    '0',
]
timings_fusion = [
    0.08, 0.14, 0.19, 0.24, 0.35, 0.39, 0.44,
    0.46, 0.55, 0.59, 0.63, 0.71,
    0.81, 0.88,
    0.92, 1.05, 1.08, 1.13,
    1.18, 1.26, 1.36, 1.37, 1.50, 1.52, 1.64,
    1.67,
]
phonetics_cat = [
    'h', 'ae', 'w', '0',
    'd', 'u', 'z',
    'th_v', 'u', '0',
    'g', 'r', 'ay', 'y', '0', 't', '0',
    'b', 'l', 'uu', 'w', '0',
    'k', 'ae', '0', 't', '0',
    'j', 'u', 'm', '0', 'p', '0',
    'j', 'ae', 'y', 'v', '0',
    'ae', 'n', 'd', '0',
    'd', 'ae', 'n', 's', '0',
    'e', 'f', 'r', 't', 'l', 'e', 's', 'l', 'y', '0',
    '0',
]
timings_cat = [
    0.10, 0.20, 0.30, 0.38,
    0.48, 0.49, 0.60,
    0.67, 0.74, 0.77,
    0.88, 0.92, 1.00, 1.04, 1.15, 1.20, 1.34,
    1.48, 1.49, 1.57, 1.66, 1.75,
    1.92, 2.03, 2.20, 2.29, 2.40,
    2.49, 2.56, 2.66, 2.73, 2.76, 2.89,
    2.99, 3.05, 3.19, 3.31, 3.38,
    3.43, 3.49, 3.55, 3.57,
    3.66, 3.69, 3.87, 3.94, 4.06,
    4.17, 4.27, 4.41, 4.46, 4.48, 4.58, 4.65, 4.84, 4.88, 4.99,
    5.05,
]

sample_rate = pe.audio.sample_rate()
run_size = pe.audio.run_size()
duration = pe.filea.duration()
samples = 0

if args.plot:
    plot = dpc.Plot()

#===== helpers =====#
def serialize_features(features):
    parts = ['{:02x}'.format(math.floor(i * 255)) for i in features]
    return ''.join([''.join(i) for i in zip(*parts)])

def bucketize(features):
    if features[0] < 0.3:
        return serialize_features(features[:5])
    else:
        return serialize_features((features[0],) + features[5:])

def render(vmodel, buckets):
    with open('phonetic_voder.i16le', 'wb') as file:
        for bucket in buckets:
            params = vmodel.params_for_bucket(bucket)
            pd.synth.synthesize(
                params['tone']['spectrum'],
                params['noise']['spectrum'],
                params['toniness'],
                0,
            )
            pd.audio.run()
            pd.tape.to_file_i16le(file)

def features_to_frame(features, vmodel):
    bucket = bucketize(features)
    transams = vmodel.params_for_bucket(bucket, features)
    return pe.frames_from_params([transams])[0]

def phonetic_to_params(phonetic):
    features = dlal.speech.get_features(model[phonetic]['frames'][0])
    return vmodel.params_for_features(features)

class Vmodel:
    def __init__(self):
        new = not os.path.exists(args.voder_model_path)
        self.conn = sqlite3.connect(args.voder_model_path)
        if new:
            statements = '''
                CREATE TABLE states (
                    bucket VARCHAR(12) PRIMARY KEY,
                    f1 REAL, -- toniness
                    f2 REAL, -- formant 1 freq
                    f3 REAL, -- formant 2 freq
                    f4 REAL, -- formant 2 freq
                    f5 REAL, -- formant 3 amp
                    f6 REAL, -- noise freq
                    f7 REAL, -- hi-freq noise amp
                    params JSONB
                );
                CREATE INDEX i_states_bucket ON states (bucket);
                CREATE INDEX i_states_f1 ON states (f1);
                CREATE INDEX i_states_f2 ON states (f2);
                CREATE INDEX i_states_f3 ON states (f3);
                CREATE INDEX i_states_f4 ON states (f4);
                CREATE INDEX i_states_f5 ON states (f5);
                CREATE INDEX i_states_f6 ON states (f6);
                CREATE INDEX i_states_f7 ON states (f7);

                CREATE TABLE phonetics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bucket VARCHAR(12),
                    phonetic VARCHAR(4),
                    freq INTEGER
                );
                CREATE INDEX i_phonetics_phonetic ON phonetics (phonetic);
                CREATE INDEX i_phonetics_bucket ON phonetics (bucket);
                CREATE INDEX i_phonetics_freq ON phonetics (freq);

                CREATE TABLE shortcuts (
                    bucket VARCHAR(12) PRIMARY KEY,
                    params JSONB
                );
            '''
            for statement in statements.split(';'):
                self.query(statement)

    #----- write -----#
    def ensure_bucket(self, bucket, features, params):
        self.query(f'''
            INSERT OR IGNORE INTO states
            VALUES (
                '{bucket}',
                {features[0]},
                {features[1]},
                {features[2]},
                {features[3]},
                {features[4]},
                {features[5]},
                {features[6]},
                '{json.dumps(params)}'
            )
        ''')

    def label_bucket(self, bucket, phonetic):
        statement = f'''
            SELECT id, freq
            FROM phonetics
            WHERE bucket = '{bucket}'
                AND phonetic = '{phonetic}'
        '''
        row = self.query_1r(statement)
        if row:
            id, freq = row
        else:
            id, freq = None, 0
        freq += 1
        if id:
            self.query(f'''
                UPDATE phonetics
                SET freq = {freq}
                WHERE id = {id}
            ''')
        else:
            self.query(f'''
                INSERT INTO phonetics (bucket, phonetic, freq)
                VALUES ('{bucket}', '{phonetic}', {freq})
            ''')

    def commit(self):
        self.conn.commit()

    #----- read -----#
    def bucket_count(self):
        return self.query_1r1c('SELECT COUNT(*) FROM states')

    def shortcut_count(self):
        return self.query_1r1c('SELECT COUNT(*) FROM shortcuts')

    def params_for_bucket(self, bucket, features=None):
        statement = f'''
            SELECT params
            FROM states
            WHERE bucket = '{bucket}'
        '''
        row = self.query_1r(statement)
        if row:
            return json.loads(row[0])
        statement = f'''
            SELECT params
            FROM shortcuts
            WHERE bucket = '{bucket}'
        '''
        row = self.query_1r(statement)
        if row:
            return json.loads(row[0])
        if features:
            params = self.params_for_features(features)
            self.query(f'''
                INSERT INTO shortcuts
                VALUES (
                    '{bucket}',
                    '{json.dumps(params)}'
                )
            ''')
            self.commit()
            return params

    def params_for_features(self, features):
        e = 1e4 / self.bucket_count()
        prev = getattr(self, '_params_for_features_prev', None)
        if prev and dlal.speech.features_distance(prev['features'], features) < e / 200:
            return self._params_for_features_prev['params']
        while True:
            toniness = features[0]
            noisiness = 1 - features[0]
            statement = f'''
                SELECT params
                FROM states
                WHERE   abs(f1 - {features[0]})               < {e}
                    AND abs(f2 - {features[1]}) * {toniness}  < {e}
                    AND abs(f3 - {features[2]}) * {toniness}  < {e}
                    AND abs(f4 - {features[3]}) * {toniness}  < {e}
                    AND abs(f5 - {features[4]}) * {toniness}  < {e}
                    AND abs(f6 - {features[5]}) * {noisiness} < {e}
                    AND abs(f7 - {features[6]}) * {noisiness} < {e}
            '''
            rows = self.query(statement)
            if len(rows) > 10: break
            e *= 1.2
        params = []
        for row in rows:
            params.append(json.loads(row[0]))
        if len(params) > 100:
            params.sort(key=lambda i: dlal.speech.features_distance(features, dlal.speech.get_features(i)))
            params = params[:100]
        result = pe.frames_from_params(params)[0]
        self._params_for_features_prev = {
            'features': features,
            'params': result,
        }
        return result

    def buckets_for_phonetic(self, phonetic, limit):
        statement = f'''
            SELECT bucket
            FROM phonetics
            WHERE phonetic = '{phonetic}'
            ORDER BY freq DESC, RANDOM()
            LIMIT {limit}
        '''
        return self.query_1c(statement)

    #----- analyze -----#
    def analyze_phonetics(self):
        ranges = []
        for phonetic in PHONETICS:
            ranges.append([])
            for i in range(7):
                ranges[-1].append([])
                for extreme in ['min', 'max']:
                    statement = f'''
                        SELECT {extreme}(f{i+1})
                        FROM phonetics p
                            JOIN states s ON s.bucket = p.bucket
                        WHERE p.phonetic = '{phonetic}'
                    '''
                    ranges[-1][-1].append(self.query_1r1c(statement))
        for phonetic, phonetic_ranges in zip(PHONETICS, ranges):
            print(phonetic)
            for i, name in enumerate(['toniness', 'f1', 'f2', 'f2_amp', 'f3_amp', 'fn', 'hi']):
                print(f'\t{name:>8} {phonetic_ranges[i][0]:>8.3f} {phonetic_ranges[i][1]:>8.3f}')

    #----- generic -----#
    def query(self, statement):
        return self.conn.execute(statement).fetchall()

    def query_1r(self, statement):
        return self.conn.execute(statement).fetchone()

    def query_1c(self, statement):
        return [i[0] for i in self.query(statement)]

    def query_1r1c(self, statement):
        row = self.query_1r(statement)
        return row and row[0]

#===== plots =====#
def plot_toniness():
    with open('assets/phonetics/model.json') as f:
        model = json.loads(f.read())
    plot = dpc.Plot()
    i = 0
    for phonetic, info in model.items():
        for j, frame in enumerate(info['frames']):
            plot.text(f'{phonetic}{j}', i, frame['toniness'])
            i += 1
    plot.show()

def plot_spectrum(phonetic, frame=0):
    with open('assets/phonetics/model.json') as f:
        model = json.loads(f.read())
    s_t = model[phonetic]['frames'][frame]['tone']['spectrum']
    s_n = model[phonetic]['frames'][frame]['noise']['spectrum']
    dpc.plot([s_n, s_t])

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
    vmodel = Vmodel()
    bucket_prev = None
    while samples < duration:
        print(f'\r{samples / duration * 100:.1f} %; {vmodel.bucket_count()} buckets', end='')
        pe.audio.run()
        sample = pe.sample_system()
        params = pe.parameterize(*sample)
        features = dlal.speech.get_features(params)
        bucket = bucketize(features)
        vmodel.ensure_bucket(bucket, features, params)
        if args.labeled:
            seconds = int(samples / 44100)
            deciseconds = int(samples / 4410)
            phonetic = None
            new = True
            # figure out what phonetic we're in, if any
            if seconds % 10 < 2:
                # before a phonetic
                new = True
                if sum(params['tone']['spectrum']) + sum(params['noise']['spectrum']) < 1.5:
                    # use as silence phonetic
                    phonetic = '0'
            elif 4 <= seconds % 10 < 9:
                # in a phonetic
                phonetic = PHONETICS[seconds // 10]
                if phonetic in STOPS:
                    # special (incomplete and incorrect) handling for stops
                    spectrum = sample[0]
                    if new and deciseconds % 100 > 88:
                        # if not much time left (<2 deciseconds), don't start a new stop
                        phonetic = None
                    else:
                        # we're continuing a stop or have enough time to start one
                        s = sum(spectrum[:len(spectrum) // 2])
                        if new:
                            # don't start until high energy
                            if s < 0.2:
                                phonetic = None
                        else:
                            # don't end until low energy
                            if s < 0.01:
                                new = True
                                phonetic = None
            # label accordingly
            if phonetic:
                vmodel.label_bucket(bucket, phonetic)
                new = False
        if args.plot:
            plot.point(samples, vmodel.bucket_count())
        bucket_prev = bucket
        samples += run_size
    print()
    vmodel.commit()

def transcode_no_buckets():
    return transcode(use_buckets=False)

def transcode(use_buckets=True):
    global samples
    with open('phonetic_voder.i16le', 'wb') as file:
        vmodel = Vmodel()
        shortcuts_i = vmodel.shortcut_count()
        while samples < duration:
            print(f'\r{samples / duration * 100:.1f} %', end='')
            pe.audio.run()
            sample = pe.sample_system()
            params = pe.parameterize(*sample)
            features = dlal.speech.get_features(params)
            if use_buckets:
                bucket = bucketize(features)
                transams = vmodel.params_for_bucket(bucket, features)
            else:
                transams = vmodel.params_for_features(features)
            amp = min(params['f'] * 10, 1)
            pd.synth.synthesize(
                [amp * i for i in transams['tone']['spectrum']],
                [amp * i for i in transams['noise']['spectrum']],
                transams['toniness'],
                0,
            )
            pd.audio.run()
            pd.tape.to_file_i16le(file)
            samples += run_size
        shortcuts_f = vmodel.shortcut_count()
        print(f'\nshortcuts: {shortcuts_i} -> {shortcuts_f}')

def generate_naive(phonetics=phonetics_ashes):
    with open('assets/phonetics/model.json') as f:
        model = json.loads(f.read())
    vmodel = Vmodel()
    smoother = dlal.speech.Smoother()
    with open('phonetic_voder.i16le', 'wb') as file:
        for phonetic in phonetics:
            print(phonetic)
            frame = model[phonetic]['frames'][0]
            for _ in range(200):
                smoothed_frame = smoother.smooth(frame, 0.99)
                features = dlal.speech.get_features(smoothed_frame)
                transframe = features_to_frame(features, vmodel)
                pd.synth.synthesize(
                    [i[0] for i in transframe['tone']['spectrum']],
                    [i[0] for i in transframe['noise']['spectrum']],
                    transframe['toniness'][0],
                    0,
                )
                pd.audio.run()
                pd.tape.to_file_i16le(file)

def generate(phonetics=phonetics_cat, timings=timings_cat, pitches=None):
    with open('assets/phonetics/model.json') as f:
        model = json.loads(f.read())
    vmodel = Vmodel()
    shortcuts_i = vmodel.shortcut_count()
    smoother = dlal.speech.Smoother()
    amp = 1e-3
    with open('phonetic_voder.i16le', 'wb') as file:
        phonetics.insert(0, '0')
        if timings == None:
            timings = [i/4 for i in range(len(phonetics))]
        elif type(timings) in [int, float]:
            timings = [i * timings for i in range(len(phonetics))]
        if pitches:
            pitches.insert(0, None)
        else:
            pitches = [None] * len(phonetics)
        params = None
        time = 0
        info_prev = None
        timings_next = timings[1:] + [None]
        for phonetic, timing, timing_next, pitch in zip(phonetics, timings, timings_next, pitches):
            print(f'{phonetic:<4} {time:>7.3f} {timing:>7.3f} {pitch if pitch else "-":>3}')
            if timing_next:
                duration = timing_next - timing
            else:
                duration = None
            if pitch:
                pd.porta.rhymel.midi([0x90, pitch, 0x7F])
            info = model[phonetic]
            if not info_prev: info_prev = info
            frames = info['frames']
            frame_i = 0
            while time < timing:
                if phonetic != '0':
                    # smoothness
                    if duration and duration < 0.1:
                        smoothness = 0.5
                    elif info['type'] == 'stop':
                        if frame_i == 0:
                            smoothness = 0
                        else:
                            smoothness = 0.7
                    elif info_prev['type'] == 'stop':
                        smoothness = 0.7
                    else:
                        if not info_prev['voiced'] and info['voiced']:
                            smoothness = 0.5
                        else:
                            smoothness = 0.9
                    # get frame from continuant or stop
                    if info['type'] == 'continuant':
                        frame = frames[0]
                    elif frame_i >= len(frames):
                        frame = {
                            **model['0']['frames'][0],
                            'amp': 1e-3,
                        }
                    else:
                        frame = frames[frame_i]
                        frame_i += 1
                    # amp
                    if info['type'] == 'stop':
                        amp = frame['amp']
                    else:
                        amp *= 1.5
                        if amp > 1: amp = 1
                    # figure params
                    smoothed_frame = smoother.smooth(frame, smoothness)
                    features = dlal.speech.get_features(smoothed_frame)
                    bucket = bucketize(features)
                    params = vmodel.params_for_bucket(bucket, features)
                else:
                    if amp > 1e-3:
                        amp /= 1.5
                if params:
                    pd.synth.synthesize(
                        [amp * i for i in params['tone']['spectrum']],
                        [amp * i for i in params['noise']['spectrum']],
                        params['toniness'],
                        0,
                    )
                pd.audio.run()
                pd.tape.to_file_i16le(file)
                time += run_size / sample_rate
            info_prev = info
    shortcuts_f = vmodel.shortcut_count()
    print(f'shortcuts: {shortcuts_i} -> {shortcuts_f}')

def interact():
    global vmodel, model
    vmodel = Vmodel()
    with open('assets/phonetics/model.json') as f:
        model = json.loads(f.read())

#===== main =====#
if __name__ == '__main__':
    eval(args.action)()
    if args.plot: plot.show()
