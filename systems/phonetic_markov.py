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
        A phonetic model. It is built atop phonetic_encoder and phonetic_decoder, but works with an independent set of files.

        Whereas a phonetic_encoder model deals with full params, a phonetic_markov model deals with reduced params, or features.

        The following actions can be performed:
        - analyze_model: print out the feature ranges for each phonetic group of a phonetic_encoder model
        - train: start or update a phonetic_markov model
        - transcode: transcode a recording with a phonetic_markov model
        - markovize: take an unmarkovized phonetic_markov model, calculate paths to different phonetics from each bucket, yielding a proper phonetic_markov model

        Example flow:
        `rm assets/phonetics/markov-model.sqlite3`
        `./do.py -r 'systems/phonetic_markov.py train --recording-path assets/phonetics/phonetics.flac --labeled'`
        `./do.py -r 'systems/phonetic_markov.py train --recording-path assets/phonetics/sample1.flac'`
        `./do.py -r 'systems/phonetic_markov.py transcode --recording-path something-you-recorded.flac'`
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
        'interact',
    ],
)
parser.add_argument('--recording-path', default='assets/phonetics/sample1.flac', help='input')
parser.add_argument('--labeled', action='store_true', help='whether the recording was created by phonetic_recorder or not')
parser.add_argument('--fuzz', action='store_true', help='fuzz when training on labeled data')
parser.add_argument('--markov-model-path', default='assets/phonetics/markov-model.sqlite3')
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

def render(mmodel, buckets):
    with open('phonetic_markov.i16le', 'wb') as file:
        for bucket in buckets:
            params = mmodel.params_for_bucket(bucket)
            pd.synth.synthesize(
                params['tone']['spectrum'],
                params['noise']['spectrum'],
                0,
            )
            pd.audio.run()
            pd.tape.to_file_i16le(file)

def features_to_frame(features, mmodel):
    bucket = bucketize(features)
    transams = mmodel.params_for_bucket(bucket, features)
    return pe.frames_from_params([transams])[0]

def phonetic_to_params(phonetic):
    features = dlal.speech.get_features(model[phonetic]['frames'][0])
    return mmodel.params_for_features(features, knn=True)

class Mmodel:
    def __init__(self):
        new = not os.path.exists(args.markov_model_path)
        self.conn = sqlite3.connect(args.markov_model_path)
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

                CREATE TABLE nexts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bucket_i VARCHAR(12),
                    bucket_f VARCHAR(12),
                    freq INTEGER
                );
                CREATE INDEX i_nexts_bucket_i ON nexts (bucket_i);
                CREATE INDEX i_nexts_bucket_f ON nexts (bucket_f);

                CREATE TABLE nexts_by_phonetic (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bucket_i VARCHAR(12),
                    bucket_f VARCHAR(12),
                    phonetic VARCHAR(4),
                    freq INTEGER,
                    distance INTEGER
                );
                CREATE INDEX i_nexts_by_phonetic_bucket_i ON nexts_by_phonetic (bucket_i);
                CREATE INDEX i_nexts_by_phonetic_phonetic ON nexts_by_phonetic (phonetic);
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

    def add_next(self, bucket_i, bucket_f):
        statement = f'''
            SELECT id, freq
            FROM nexts
            WHERE bucket_i = '{bucket_i}'
                AND bucket_f = '{bucket_f}'
        '''
        row = self.query_1r(statement)
        if row:
            id, freq = row
        else:
            id, freq = None, 0
        freq += 1
        if id:
            self.query(f'''
                UPDATE nexts
                SET freq = {freq}
                WHERE id = {id}
            ''')
        else:
            self.query(f'''
                INSERT INTO nexts (bucket_i, bucket_f, freq)
                VALUES ('{bucket_i}', '{bucket_f}', {freq})
            ''')

    def clear_nexts_by_phonetic(self):
        self.query('DELETE FROM nexts_by_phonetic')

    def set_next_by_phonetic(self, bucket_i, bucket_f, phonetic, freq, distance):
        self.query(f'''
            INSERT INTO nexts_by_phonetic (bucket_i, bucket_f, phonetic, freq, distance)
            VALUES ('{bucket_i}', '{bucket_f}', '{phonetic}', {freq}, {distance})
        ''')

    def commit(self):
        self.conn.commit()

    #----- read -----#
    def bucket_count(self):
        return self.query_1r1c('SELECT COUNT(*) FROM states')

    def params_for_bucket(self, bucket, features=None):
        statement = f'''
            SELECT params
            FROM states
            WHERE bucket = '{bucket}'
        '''
        row = self.query_1r(statement)
        if row:
            return json.loads(row[0])
        if features:
            return self.params_for_features(features)

    def params_for_features(self, features, knn=False):
        e = 1e4 / self.bucket_count()
        prev = getattr(self, '_params_for_features_prev', None)
        if prev and dlal.speech.features_distance(prev['features'], features) < e / 20:
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
        if not knn:
            d_min = math.inf
            for row in rows:
                params = json.loads(row[0])
                d = dlal.speech.features_distance(features, dlal.speech.get_features(params))
                if d < d_min:
                    result = params
                    d_min = d
        else:
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

    def bucket_count_for_phonetic(self, phonetic):
        statement = f'''
            SELECT COUNT(*)
            FROM phonetics
            WHERE phonetic = '{phonetic}'
        '''
        return self.query_1r1c(statement)

    def buckets_for_phonetic(self, phonetic, limit):
        statement = f'''
            SELECT bucket
            FROM phonetics
            WHERE phonetic = '{phonetic}'
            ORDER BY freq DESC, RANDOM()
            LIMIT {limit}
        '''
        return self.query_1c(statement)

    def nexts_for_bucket(self, bucket):
        statement = f'''
            SELECT bucket_f, freq
            FROM nexts
            WHERE bucket_i = '{bucket}'
        '''
        return self.query(statement)

    def prevs_for_bucket(self, bucket):
        statement = f'''
            SELECT bucket_i
            FROM nexts
            WHERE bucket_f = '{bucket}'
        '''
        return self.query_1c(statement)

    def phonetic_freq_for_bucket(self, bucket, phonetic):
        statement = f'''
            SELECT freq
            FROM phonetics
            WHERE bucket = '{bucket}'
        '''
        row = self.query_1r(statement)
        return row and row[0] or 0

    def freqs_for_next_by_phonetic(self, bucket, phonetic):
        statement = f'''
            SELECT bucket_f, freq
            FROM nexts_by_phonetic
            WHERE bucket_i = '{bucket}'
                AND phonetic = '{phonetic}'
        '''
        return self.query(statement)

    #----- analyze -----#
    def max_intraphonetic_distance(self, phonetic):
        statement = f'''
            SELECT max(n.distance)
            FROM phonetics p
                JOIN nexts_by_phonetic n ON n.bucket_i = p.bucket
            WHERE p.phonetic = '{phonetic}'
                AND n.phonetic = '{phonetic}'
        '''
        return self.query_1r1c(statement)

    def max_intraphonetic_distances(self):
        for phonetic in PHONETICS:
            d = self.max_intraphonetic_distance(phonetic)
            print(f'{phonetic:4} {d}')

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
    mmodel = Mmodel()
    bucket_prev = None
    while samples < duration:
        print(f'\r{samples / duration * 100:.1f} %; {mmodel.bucket_count()} buckets', end='')
        pe.audio.run()
        sample = pe.sample_system()
        params = pe.parameterize(*sample)
        features = dlal.speech.get_features(params)
        bucket = bucketize(features)
        mmodel.ensure_bucket(bucket, features, params)
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
                mmodel.label_bucket(bucket, phonetic)
                new = False
        if bucket_prev:
            mmodel.add_next(bucket_prev, bucket)
        if args.plot:
            plot.point(samples, mmodel.bucket_count())
        bucket_prev = bucket
        samples += run_size
    if args.fuzz:
        for phonetic in PHONETICS:
            statement = f'''
                SELECT sum(freq)
                FROM phonetics
                WHERE freq > 1 AND phonetic = '{phonetic}'
            '''
            if (mmodel.query_1r1c(statement) or 0) > 100: continue
            buckets = mmodel.buckets_for_phonetic(phonetic, 100)
            for bucket_i, bucket_f in zip(buckets, buckets[1:]):
                mmodel.add_next(bucket_i, bucket_f)
    print()
    mmodel.commit()

def transcode():
    global samples
    with open('phonetic_markov.i16le', 'wb') as file:
        mmodel = Mmodel()
        while samples < duration:
            print(f'\r{samples / duration * 100:.1f} %', end='')
            pe.audio.run()
            sample = pe.sample_system()
            params = pe.parameterize(*sample)
            features = dlal.speech.get_features(params)
            transams = mmodel.params_for_features(features)
            amp = 1e2 * math.sqrt(sum(i**2 for i in sample[0]))
            pd.synth.synthesize(
                [amp * i for i in transams['tone']['spectrum']],
                [amp * i for i in transams['noise']['spectrum']],
                0,
            )
            pd.audio.run()
            pd.tape.to_file_i16le(file)
            samples += run_size
    print()

def generate_naive(phonetics=phonetics_ashes):
    with open('assets/phonetics/model.json') as f:
        model = json.loads(f.read())
    mmodel = Mmodel()
    smoother = dlal.speech.Smoother()
    with open('phonetic_markov.i16le', 'wb') as file:
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

def markovize():
    mmodel = Mmodel()
    mmodel.clear_nexts_by_phonetic()
    for phonetic in PHONETICS + ['0']:
        print(phonetic)
        visited = set()
        bucket_count = mmodel.bucket_count_for_phonetic(phonetic)
        buckets = mmodel.buckets_for_phonetic(phonetic, max(bucket_count // 100, 10))
        # steady-state transitions
        for k in buckets:
            for n, freq_t in mmodel.nexts_for_bucket(k):
                freq_s = mmodel.phonetic_freq_for_bucket(n, phonetic)
                if freq_s:
                    mmodel.set_next_by_phonetic(k, n, phonetic, freq_t, 0)
                    visited.add(k)
        # transient transitions
        queue = [(k, 1) for k in buckets]
        while queue:
            k, distance = queue[0]
            queue = queue[1:]
            ps = mmodel.prevs_for_bucket(k)
            for p in ps:
                if p in visited: continue
                mmodel.set_next_by_phonetic(p, k, phonetic, 1, distance)
                queue.append((p, distance + 1))
                visited.add(p)
    mmodel.commit()

def generate(phonetics=phonetics_ashes, timings=None):
    with open('assets/phonetics/model.json') as f:
        model = json.loads(f.read())
    mmodel = Mmodel()
    smoother = dlal.speech.Smoother()
    amp = 1e-3
    with open('phonetic_markov.i16le', 'wb') as file:
        phonetics.insert(0, '0')
        if timings == None:
            timings = [i/4 for i in range(len(phonetics))]
        elif type(timings) in [int, float]:
            timings = [i * timings for i in range(len(phonetics))]
        params = None
        time = 0
        for phonetic, timing in zip(phonetics, timings):
            print(phonetic)
            frame = model[phonetic]['frames'][0]
            while time < timing:
                if phonetic != '0':
                    smoothed_frame = smoother.smooth(frame, 0.9)
                    features = dlal.speech.get_features(smoothed_frame)
                    params = mmodel.params_for_features(features, knn=True)
                    amp *= 1.1
                    if amp > 1: amp = 1
                else:
                    if amp > 1e-3:
                        amp /= 1.1
                if params:
                    pd.synth.synthesize(
                        [amp * i[0] for i in params['tone']['spectrum']],
                        [amp * i[0] for i in params['noise']['spectrum']],
                        0,
                    )
                pd.audio.run()
                pd.tape.to_file_i16le(file)
                time += run_size / sample_rate

def interact():
    global mmodel, model
    mmodel = Mmodel()
    with open('assets/phonetics/model.json') as f:
        model = json.loads(f.read())

#===== main =====#
eval(args.action)()
if args.plot: plot.show()
