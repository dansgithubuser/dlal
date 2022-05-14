import dlal

import dansplotcore as dpc

import argparse
import json
import math

parser = argparse.ArgumentParser()
parser.add_argument('action',
    choices=[
        'continuants',
        'stops',
        'formants',
    ],
    default='continuants',
    nargs='?',
)
args = parser.parse_args()

model = dlal.speech.Model('assets/local/phonetic-model.json')

def log(x, e=4):
    if x < 10 ** -e: return 0
    return (math.log10(x) + e) / e

if args.action == 'continuants':
    mean_spectra = json.load(open('assets/local/mean-spectra.json'))
    plot = dpc.Plot()
    for phonetic_i, (phonetic, info) in enumerate(model.phonetics.items()):
        if info['type'] == 'stop' or phonetic == '0': continue
        x = phonetic_i * 2
        # label
        plot.text(phonetic, x, -100)
        # spectrum
        mean_spectrum = mean_spectra[phonetic]
        for bin_i, (amp_a, amp_b) in enumerate(zip(mean_spectrum, mean_spectrum[1:])):
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
            noise_bin_per_stft_bin = model.noise_bins / (model.stft_bins / 2)
            noise_spectrum = info['frames'][0]['noise']['spectrum']
            for bin_i, (amp_a, amp_b) in enumerate(zip(noise_spectrum, noise_spectrum[1:])):
                amp_a *= noise_bin_per_stft_bin
                amp_b *= noise_bin_per_stft_bin
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

if args.action == 'stops':
    plot = dpc.Plot()
    x = 0
    for phonetic, info in model.phonetics.items():
        if info['type'] != 'stop': continue
        plot.text(phonetic, x, -100)  # label
        for frame in info['frames']:
            spectrum = frame['noise']['spectrum']
            for bin_i, amp in enumerate(spectrum):
                plot.rect(
                    x+0,
                    (bin_i+0) * model.freq_per_bin_noise,
                    x+1,
                    (bin_i+1) * model.freq_per_bin_noise,
                    a=log(amp, 4),
                )
            x += 1
        x += 1
    plot.show()

if args.action == 'formants':
    formant_paths = json.load(open('assets/local/formant-paths.json'))
    plot = dpc.Plot()
    x = 0
    for phonetic, info in model.phonetics.items():
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
