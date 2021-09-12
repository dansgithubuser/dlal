import argparse
import collections
import json
import math
import os
import random
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
    ],
)
parser.add_argument('--recording-path', default='assets/phonetics/sample1.flac', help='input')
parser.add_argument('--labeled', action='store_true', help='whether the recording was created by phonetic_recorder or not')
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
    return ''.join(['{:03x}'.format(math.floor(i * 2048)) for i in features])

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
    transams = mmodel.params_for_bucket(bucket, features)
    return pe.frames_from_params([transams])[0]

class Mmodel:
    def __init__(self):
        new = not os.path.exists(args.markov_model_path)
        self.conn = sqlite3.connect(args.markov_model_path)
        if new:
            statements = '''
                CREATE TABLE states (
                    bucket VARCHAR(12) PRIMARY KEY,
                    f1 REAL,
                    f2 REAL,
                    f3 REAL,
                    f4 REAL,
                    f5 REAL,
                    f6 REAL,
                    f7 REAL,
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
                    freq INTEGER
                );
                CREATE INDEX i_nexts_by_phonetic_bucket_i ON nexts_by_phonetic (bucket_i);
                CREATE INDEX i_nexts_by_phonetic_phonetic ON nexts_by_phonetic (phonetic);
            '''
            for statement in statements.split(';'):
                self.conn.execute(statement)

    #----- write -----#
    def ensure_bucket(self, bucket, features, params):
        self.conn.execute(f'''
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
        row = self.conn.execute(statement).fetchone()
        if row:
            id, freq = row
        else:
            id, freq = None, 0
        freq += 1
        if id:
            self.conn.execute(f'''
                UPDATE phonetics
                SET freq = {freq}
                WHERE id = {id}
            ''')
        else:
            self.conn.execute(f'''
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
        row = self.conn.execute(statement).fetchone()
        if row:
            id, freq = row
        else:
            id, freq = None, 0
        freq += 1
        if id:
            self.conn.execute(f'''
                UPDATE nexts
                SET freq = {freq}
                WHERE id = {id}
            ''')
        else:
            self.conn.execute(f'''
                INSERT INTO nexts (bucket_i, bucket_f, freq)
                VALUES ('{bucket_i}', '{bucket_f}', {freq})
            ''')

    def clear_nexts_by_phonetic(self):
        self.conn.execute('DELETE FROM nexts_by_phonetic')

    def set_next_by_phonetic(self, bucket_i, bucket_f, phonetic, freq):
        self.conn.execute(f'''
            INSERT INTO nexts_by_phonetic (bucket_i, bucket_f, phonetic, freq)
            VALUES ('{bucket_i}', '{bucket_f}', '{phonetic}', {freq})
        ''')

    def commit(self):
        self.conn.commit()

    #----- read -----#
    def bucket_count(self):
        return self.conn.execute('SELECT COUNT(*) FROM states').fetchone()[0]

    def params_for_bucket(self, bucket, features=None):
        statement = f'''
            SELECT params
            FROM states
            WHERE bucket = '{bucket}'
        '''
        row = self.conn.execute(statement).fetchone()
        if row:
            return json.loads(row[0])
        if features:
            return self.params_for_features(features)

    def params_for_features(self, features):
        e = 1e4 / self.bucket_count()
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
            rows = self.conn.execute(statement).fetchall()
            if len(rows) > 10: break
            e *= 2
        d_min = math.inf
        for row in rows:
            params = json.loads(row[0])
            d = dlal.speech.features_distance(features, dlal.speech.get_features(params))
            if d < d_min:
                result = params
                d_min = d
        return result

    def buckets_for_phonetic(self, phonetic, limit):
        statement = f'''
            SELECT bucket
            FROM phonetics
            WHERE phonetic = '{phonetic}'
            ORDER BY freq DESC
            LIMIT {limit}
        '''
        return [i[0] for i in self.conn.execute(statement).fetchall()]

    def nexts_for_bucket(self, bucket):
        statement = f'''
            SELECT bucket_f, freq
            FROM nexts
            WHERE bucket_i = '{bucket}'
        '''
        return self.conn.execute(statement).fetchall()

    def prevs_for_bucket(self, bucket):
        statement = f'''
            SELECT bucket_i
            FROM nexts
            WHERE bucket_f = '{bucket}'
        '''
        return [i[0] for i in self.conn.execute(statement).fetchall()]

    def phonetic_freq_for_bucket(self, bucket, phonetic):
        statement = f'''
            SELECT freq
            FROM phonetics
            WHERE bucket = '{bucket}'
        '''
        row = self.conn.execute(statement).fetchone()
        return row and row[0] or 0

    def freqs_for_next_by_phonetic(self, bucket, phonetic):
        statement = f'''
            SELECT bucket_f, freq
            FROM nexts_by_phonetic
            WHERE bucket_i = '{bucket}'
                AND phonetic = '{phonetic}'
        '''
        return self.conn.execute(statement).fetchall()

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
                mmodel.label_bucket(bucket, phonetic)
                new = False
        if bucket_prev:
            mmodel.add_next(bucket_prev, bucket)
        if args.plot:
            plot.point(samples, mmodel.bucket_count())
        bucket_prev = bucket
        samples += run_size
    print()
    mmodel.commit()

def transcode():
    global samples
    file = open('phonetic_markov.i16le', 'wb')
    mmodel = Mmodel()
    while samples < duration:
        print(f'\r{samples / duration * 100:.1f} %', end='')
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
    print()

def generate_naive(phonetics=phonetics_ashes):
    file = open('phonetic_markov.i16le', 'wb')
    with open('assets/phonetics/model.json') as f:
        model = json.loads(f.read())
    mmodel = Mmodel()
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
    mmodel = Mmodel()
    mmodel.clear_nexts_by_phonetic()
    for phonetic in PHONETICS + ['0']:
        print(phonetic)
        visited = set()
        buckets = mmodel.buckets_for_phonetic(phonetic, 10)
        # steady-state transitions
        for k in buckets:
            for n, freq_t in mmodel.nexts_for_bucket(k):
                freq_s = mmodel.phonetic_freq_for_bucket(n, phonetic)
                if freq_s:
                    mmodel.set_next_by_phonetic(k, n, phonetic, freq_t)
                    visited.add(k)
        # transient transitions
        queue = buckets
        while queue:
            k = queue[0]
            queue = queue[1:]
            ps = mmodel.prevs_for_bucket(k)
            for p in ps:
                if p in visited: continue
                mmodel.set_next_by_phonetic(p, k, phonetic, 1)
                queue.append(p)
                visited.add(p)
    mmodel.commit()

def generate(phonetics=phonetics_ashes):
    mmodel = Mmodel()
    k = mmodel.buckets_for_phonetic('0', 1)[0]
    file = open('phonetic_markov.i16le', 'wb')
    for phonetic in phonetics:
        print(phonetic)
        for i in range(200):
            params = mmodel.params_for_bucket(k)
            pd.synth.synthesize(
                params['tone']['spectrum'],
                params['noise']['spectrum'],
                0,
            )
            pd.audio.run()
            pd.tape.to_file_i16le(file)
            nexts = mmodel.freqs_for_next_by_phonetic(k, phonetic)
            k = random.sample([i[0] for i in nexts], 1, counts=[i[1] for i in nexts])[0]

#===== main =====#
eval(args.action)()
if args.plot: plot.show()
