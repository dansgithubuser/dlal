import argparse
import json
import math
import os

parser = argparse.ArgumentParser()
parser.add_argument('recording_path')
parser.add_argument('--save-params-to')
parser.add_argument('--transcode-params-from')
args = parser.parse_args()

os.environ['PHONETIC_ENCODER_RECORDING_PATH'] = args.recording_path
import dlal
import phonetic_encoder as pe
dlal.comm_set(None)
import phonetic_decoder as pd

try:
    import dansplotcore as dpc

    def get_features(params):
        return (
            dlal.speech.get_param(params, ['tone', 'formants', 1, 'freq']) / 1000,
            (dlal.speech.get_param(params, ['tone', 'formants', 2, 'freq']) - 1000) / 1000,
            dlal.speech.get_param(params, ['noise', 'freq_c']) / 10000,
            dlal.speech.get_param(params, ['noise', 'hi']),
        )

    def features_to_xy(features):
        bases = []
        for i in range(len(features)):
            t = i / len(features) * math.pi
            bases.append((math.cos(t), math.sin(t)))
        x = sum(i * j[0] for i, j in zip(features, bases))
        y = sum(i * j[1] for i, j in zip(features, bases))
        return x, y

    def features_to_rgb(features):
        r = 0.05 + features[0] / 2 + features[3] / 2
        g = 0.25 + features[1]
        b = 0.25 + min(features[2], 0.75)
        return r, g, b

    class Plotter:
        def __init__(self):
            self.plot = dpc.Plot()
            self.xy_prev = None

        def add(self, params):
            features = get_features(params)
            x, y = features_to_xy(features)
            r, g, b = features_to_rgb(features)
            s = 0.002
            self.plot.rect(
                x - s, y - s,
                x + s, y + s,
                r, g, b, 0.5,
            )
            if self.xy_prev: self.plot.line(
                *self.xy_prev,
                x, y,
                r, g, b, 0.5,
            )
            self.xy_prev = x, y

        def plot_model(self, model):
            for phonetic, info in model.items():
                features = get_features(info['frames'][0])
                self.plot.text(
                    phonetic,
                    *features_to_xy(features),
                    *features_to_rgb(features),
                )

        def show(self):
            self.plot.show()
except:
    class Plotter:
        def add(self, params): pass
        def show(self): pass

run_size = pe.audio.run_size()
duration = pe.filea.duration()
samples = 0
file = open('phonetic_vocoder.i16le', 'wb')
plotter = Plotter()
paramses = []
if args.transcode_params_from:
    with open(args.transcode_params_from) as f:
        transamses = json.loads(f.read())
    transam_ds = []
else:
    transamses = None

while samples < duration:
    pe.audio.run()
    sample = pe.sample_system()
    params = pe.parameterize(*sample)
    extra_info = ''
    if transamses:
        d_min = math.inf
        transams_min = None
        for transams in transamses:
            d = dlal.speech.params_distance(params, transams)
            if d < d_min:
                transams_min = transams
                d_min = d
        params = transams_min
        transam_ds.append(d_min)
        extra_info += f'd: {d_min:9>.3}'
    plotter.add(params)
    paramses.append(params)
    frame = pe.frames_from_params([params])[0]
    pd.synth.synthesize(
        [i[0] for i in frame['tone']['spectrum']],
        [i[0] for i in frame['noise']['spectrum']],
        0,
    )
    pd.audio.run()
    pd.tape.to_file_i16le(file)
    samples += run_size
    t = samples / 44100
    f1 = dlal.speech.get_param(params, ['tone', 'formants', 1, 'freq'])
    f2 = dlal.speech.get_param(params, ['tone', 'formants', 2, 'freq'])
    f3 = dlal.speech.get_param(params, ['tone', 'formants', 3, 'freq'])
    fc = dlal.speech.get_param(params, ['noise', 'freq_c'])
    hi = dlal.speech.get_param(params, ['noise', 'hi'])
    toniness = dlal.speech.get_param(params, ['toniness'])
    print(
        f't: {t:>5.3f} s, '
        f'f1: {f1:>5.0f} Hz, '
        f'f2: {f2:>5.0f} Hz, '
        f'f3: {f3:>5.0f} Hz, '
        f'fc: {fc:>5.0f} Hz, '
        f'hi: {hi:>5.3f}, '
        f'toniness: {toniness:>5.3f}, '
        f'{extra_info}'
    )

if args.save_params_to:
    with open(args.save_params_to, 'w') as f:
        f.write(json.dumps(paramses))

plotter.plot_model(pd.phonetizer.model)
plotter.show()
