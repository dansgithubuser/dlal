import dlal

import dansplotcore as dpc

import argparse
import json
import math

parser = argparse.ArgumentParser()
parser.add_argument('action',
    choices=[
        'plot-tone-features',
    ],
    default='plot-tone-features',
    nargs='?',
)
args = parser.parse_args()

model = dlal.speech.Model('assets/local/phonetic-model.json')
mean_spectra = json.load(open('assets/local/mean-spectra.json'))

def log(x, e=4):
    if x < 10 ** -e: return 0
    return (math.log10(x) + e) / e

if args.action == 'plot-tone-features':
    plot = dpc.Plot()
    for phonetic_i, (phonetic, info) in enumerate(model.phonetics.items()):
        if not info['voiced'] or info['type'] == 'stop': continue
        x = phonetic_i * 2
        # label
        plot.text(phonetic, x, -100)
        # spectrum
        mean_spectrum = mean_spectra[phonetic]
        amp_max = max(mean_spectrum)
        for bin_i, (amp_a, amp_b) in enumerate(zip(mean_spectrum, mean_spectrum[1:])):
            amp_a /= amp_max
            amp_b /= amp_max
            plot.line(
                x+log(amp_a),
                (bin_i+0) * model.freq_per_bin,
                x+log(amp_b),
                (bin_i+1) * model.freq_per_bin,
            )
        # formants
        for formant in info['frames'][0]['tone']['formants']:
            freq = formant['freq']
            amp = log(formant['amp'], 2)
            plot.line(x, freq, x+amp, freq, r=1.0, g=amp, b=0.0)
    plot.show()
