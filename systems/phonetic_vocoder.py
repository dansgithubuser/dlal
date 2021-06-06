import argparse
import math
import os

parser = argparse.ArgumentParser()
parser.add_argument('recording_path', nargs='?', default='assets/phonetics/phonetics.flac')
args = parser.parse_args()

os.environ['PHONETIC_ENCODER_RECORDING_PATH'] = args.recording_path
import dlal
import phonetic_encoder as pe
dlal.comm_set(None)
import phonetic_decoder as pd

try:
    import dansplotcore as dpc

    def params_to_xy(params):
        features = [
            params['tone']['formants'][1]['freq'] / 2000,
            params['tone']['formants'][2]['freq'] / 2000,
            params['noise']['freq_peak'] / 44100 * params['noise']['amp_peak'] * 100,
        ]
        bases = []
        for i in range(len(features)):
            t = i / len(features) * math.pi
            bases.append((math.cos(t), math.sin(t)))
        x = sum(i * j[0] for i, j in zip(features, bases))
        y = sum(i * j[1] for i, j in zip(features, bases))
        return x, y

    def params_to_rgb(params):
        r = 0.25 + params['tone']['formants'][1]['freq'] / 2000
        g = 0.25 + (params['tone']['formants'][2]['freq'] - 1000) / 2000
        b = 0.25 + min(params['noise']['freq_peak'] / 44100 * params['noise']['amp_peak'] * 100, 0.75)
        return r, g, b

    class Plotter:
        def __init__(self):
            self.plot = dpc.Plot()
            self.params_prev = None

        def add(self, params):
            x, y = params_to_xy(params)
            r = 0.002
            self.plot.rect(
                x - r, y - r,
                x + r, y + r,
                *params_to_rgb(params),
                a=0.5,
            )
            self.params_prev = params

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

while samples < duration:
    pe.audio.run()
    sample = pe.sample_system()
    params = pe.parameterize(*sample)
    plotter.add(params)
    frame = pe.frames_from_params([params])[0]
    pd.phonetizer.say_frame(frame)
    pd.audio.run()
    pd.tape.to_file_i16le(file)
    samples += run_size

plotter.show()
