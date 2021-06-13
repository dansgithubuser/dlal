import argparse
import json
import math
import os

parser = argparse.ArgumentParser()
parser.add_argument('recording_path', nargs='?', default='assets/phonetics/phonetics.flac')
parser.add_argument('--save-params-to')
parser.add_argument('--transcode-params-from')
parser.add_argument('--normalize', action='store_true')
args = parser.parse_args()

os.environ['PHONETIC_ENCODER_RECORDING_PATH'] = args.recording_path
import dlal
import phonetic_encoder as pe
dlal.comm_set(None)
import phonetic_decoder as pd

try:
    import dansplotcore as dpc

    def get_param(params, ks):
        x = params
        for k in ks: x = x[k]
        if type(x) == list: x = x[0]
        return x

    def get_features(params):
        return (
            get_param(params, ['tone', 'formants', 1, 'freq']) / 1000,
            (get_param(params, ['tone', 'formants', 2, 'freq']) - 1000) / 1000,
            get_param(params, ['noise', 'freq_peak']) / 10000,
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
        r = 0.25 + features[0]
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

def params_distance(a, b):
    # a
    a_tone_amp = get_param(a, ['tone', 'amp'])
    a_noise_amp = get_param(a, ['noise', 'amp'])
    a_toniness = a_tone_amp / (a_tone_amp + a_noise_amp)
    a_f1 = get_param(a, ['tone', 'formants', 1, 'freq']) / 1000
    a_f2 = (get_param(a, ['tone', 'formants', 2, 'freq']) - 1000) / 1000
    a_fn = get_param(a, ['noise', 'freq_peak']) / 10000
    # b
    b_tone_amp = get_param(b, ['tone', 'amp'])
    b_noise_amp = get_param(b, ['noise', 'amp'])
    b_toniness = b_tone_amp / (b_tone_amp + b_noise_amp)
    b_f1 = get_param(b, ['tone', 'formants', 1, 'freq']) / 1000
    b_f2 = (get_param(b, ['tone', 'formants', 2, 'freq']) - 1000) / 1000
    b_fn = get_param(b, ['noise', 'freq_peak']) / 10000
    # d
    d_tone = (a_f1 - b_f1) ** 2 + (a_f2 - b_f2) ** 2
    d_noise = (a_fn - b_fn) ** 2
    d = d_tone * max(a_toniness, b_toniness) + d_noise * (1 - min(a_toniness, b_toniness))
    #
    return d

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
    if transamses:
        d_min = math.inf
        transams_min = None
        for transams in transamses:
            d = params_distance(params, transams)
            if d < d_min:
                transams_min = transams
                d_min = d
        params = transams_min
        transam_ds.append(d_min)
    if args.normalize:
        e = sum([
            sum(i ** 2 for i in params['tone']['spectrum']),
            sum(i ** 2 for i in params['noise']['spectrum']),
        ])
        params['tone']['spectrum'] = [i/math.sqrt(e) for i in params['tone']['spectrum']]
        params['noise']['spectrum'] = [i/math.sqrt(e) for i in params['noise']['spectrum']]
    plotter.add(params)
    paramses.append(params)
    frame = pe.frames_from_params([params])[0]
    pd.phonetizer.say_frame(frame)
    pd.audio.run()
    pd.tape.to_file_i16le(file)
    samples += run_size
    print(f'{samples / duration * 100:.2f} %')

if args.save_params_to:
    with open(args.save_params_to, 'w') as f:
        f.write(json.dumps(paramses))

plotter.plot_model(pd.phonetizer.model)
plotter.show()
