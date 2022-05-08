import dlal

import dansplotcore as dpc

import argparse
import json
import math

parser = argparse.ArgumentParser()
parser.add_argument('action',
    choices=[
        'plot-tone-features',
        'plot-formant-paths',
    ],
    default='plot-tone-features',
    nargs='?',
)
args = parser.parse_args()

model = dlal.speech.Model('assets/local/phonetic-model.json')

def log(x, e=4):
    if x < 10 ** -e: return 0
    return (math.log10(x) + e) / e

if args.action == 'plot-tone-features':
    mean_spectra = json.load(open('assets/local/mean-spectra.json'))
    plot = dpc.Plot()
    for phonetic_i, (phonetic, info) in enumerate(model.phonetics.items()):
        if info['type'] == 'stop' or phonetic == '0': continue
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
        # noise
        if info['fricative']:
            amp_max *= (model.stft_bins / 2) / model.noise_bins
            noise_spectrum = info['frames'][0]['noise']['spectrum']
            for bin_i, (amp_a, amp_b) in enumerate(zip(noise_spectrum, noise_spectrum[1:])):
                amp_a /= amp_max
                amp_b /= amp_max
                plot.line(
                    x+log(amp_a),
                    (bin_i+0) * model.freq_per_bin_noise,
                    x+log(amp_b),
                    (bin_i+1) * model.freq_per_bin_noise,
                    r=0,
                    g=1.0,
                    b=1.0,
                )
    plot.show()

if args.action == 'plot-formant-paths':
    formant_paths = json.load(open('assets/local/formant-paths.json'))
    plot = dpc.Plot()
    x = 0
    for phonetic_i, (phonetic, info) in enumerate(model.phonetics.items()):
        if not info['voiced'] or info['type'] == 'stop': continue
        plot.text(phonetic, x, -100)  # label
        formants_prev = None
        for v in formant_paths[phonetic]:
            spectrum = v['spectrum']
            formants = v['formants']
            # spectrum
            amp_max = max(spectrum)
            for bin_i, amp in enumerate(spectrum):
                amp_n = amp / amp_max
                plot.rect(
                    x+0,
                    (bin_i+0) * model.freq_per_bin,
                    x+1,
                    (bin_i+1) * model.freq_per_bin,
                    a=log(amp_n, 3),
                )
            # formants
            for formant in formants:
                freq = formant['freq']
                amp = log(formant['amp'], 2)
                plot.line(x, freq, x+amp, freq, r=1.0, g=amp, b=0.0)
            if formants_prev:
                for a, b in zip(formants_prev, formants):
                    plot.line(
                        x-1,
                        a['freq'],
                        x,
                        b['freq'],
                        r=1.0,
                        g=0,
                        b=0,
                    )
            formants_prev = formants
            #
            x += 1
        x += 1
    plot.show()
