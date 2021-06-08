import argparse
import json
import math
import os

parser = argparse.ArgumentParser()
parser.add_argument('recording_path', nargs='?', default='assets/phonetics/phonetics.flac')
parser.add_argument('--save-params-to')
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
            get_param(params, ['tone', 'formants', 1, 'freq']) / 2000 * get_param(params, ['tone', 'formants', 1, 'amp']) * 10,
            (get_param(params, ['tone', 'formants', 2, 'freq']) - 1000) / 2000 * get_param(params, ['tone', 'formants', 2, 'amp']) * 10,
            get_param(params, ['noise', 'freq_peak']) / 44100 * get_param(params, ['noise', 'amp_peak']) * 100,
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

run_size = pe.audio.run_size()
duration = pe.filea.duration()
samples = 0
file = open('phonetic_vocoder.i16le', 'wb')
plotter = Plotter()
paramses = []

while samples < duration:
    pe.audio.run()
    sample = pe.sample_system()
    params = pe.parameterize(*sample)
    paramses.append(params)
    plotter.add(params)
    frame = pe.frames_from_params([params])[0]
    pd.phonetizer.say_frame(frame)
    pd.audio.run()
    pd.tape.to_file_i16le(file)
    samples += run_size

if args.save_params_to:
    with open(args.save_params_to, 'w') as f:
        f.write(json.dumps(paramses))

plotter.plot_model(pd.phonetizer.model)
plotter.show()
