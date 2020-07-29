#===== imports =====#
import dlal

import argparse
import json
import math
import os
import re

try:
    import dansplotcore as dpc
except:
    pass

#===== args =====#
parser = argparse.ArgumentParser(description=
    'Takes a sound as recorded by phonetic_recorder.py, '
    'and transforms into phonetic parameters that can be consumed by phonetic_decoder.py.'
)
parser.add_argument('--phonetics-file-path', default='assets/phonetics/phonetics.flac')
parser.add_argument('--only')
parser.add_argument('--start-from')
parser.add_argument('--order', type=int, default=24)
parser.add_argument('--plot-spectra', action='store_true')
args = parser.parse_args()

#===== consts =====#
SAMPLE_RATE = 44100

#===== helpers =====#
def load(phonetics_file_path, start, duration):
    if not load.phonetics:
        load.phonetics = dlal.read_sound(phonetics_file_path)[0]
    return load.phonetics[start:start+duration]
load.phonetics = None

def autocorrelation(x, shift):
    assert len(x) > shift
    return sum(i * j for i, j in zip(x[:-shift], x[shift:]))

def stop_ranges(x):
    window_size = 512
    silence_factor = 4
    # estimate envelope
    total_amp = sum(abs(i) for i in x[:window_size])
    envelope = [total_amp / window_size]
    for i in range(window_size, len(x)):
        total_amp += abs(x[i]) - abs(x[i - window_size])
        envelope.append(total_amp / window_size)
    # figure threshold
    sorted_envelope = sorted(envelope)
    threshold = sorted_envelope[len(envelope) // silence_factor]
    # if threshold is close to maximum, this isn't a stop
    maximum = sorted_envelope[-1]
    if threshold / maximum > 1 / silence_factor:
        return None
    # figure stop starts
    result = []
    silent = True
    for i, v in enumerate(envelope):
        if silent:
            if v > maximum * 3 / 4:
                result.append([i + window_size // 2])
                silent = False
        else:
            if v < maximum / 4:
                result[-1].append(i + window_size // 2)
                silent = True
    return result

def plot_residual_spectrum(plot, actual, past, b, a, residual_size=4096):
    if plot == None:
        plot = dpc.Plot()
    from numpy.fft import fft
    coeffs = [[float(i)] for i in a[1:]]
    residual = actual[:residual_size] - past[:residual_size].dot(coeffs)
    residual = [float(i/b[0]) for i in residual]
    plot.plot([
        math.log10(float(abs(i)))
        for i in fft(residual)[0:2049]
    ])
    return plot

def plot_filter_spectrum(plot, b, a):
    if plot == None:
        plot = dpc.Plot()
    from scipy import signal
    w, h = signal.freqz(b, a)
    plot.plot([float(abs(i)) for i in h])
    return plot

def plot_pole_zero(plot, z, p):
    if plot == None:
        plot = dpc.Plot()
    for i in range(1000):
        x = math.cos(2*math.pi*i/1000)
        y = math.sin(2*math.pi*i/1000)
        plot.point(x=x, y=y, r=0, g=0)
    for zero in z:
        plot.line(xi=0, yi=0, xf=zero.real, yf=zero.imag, r=0, b=0)
    for pole in p:
        plot.line(xi=0, yi=0, xf=pole.real, yf=pole.imag, g=0, b=0)
    return plot

def parameterize(x):
    import numpy as np
    from scipy import signal
    #----- coeffs -----#
    past = np.array([
        x[i:i+args.order]
        for i in range(len(x) - args.order)
    ])
    actual = np.array([
        [x[i+args.order]]
        for i in range(len(x) - args.order)
    ])
    coeffs = np.linalg.pinv(past).dot(actual)
    #----- stabilize and smooth -----#
    b = [1]
    a = [1] + [i for i in coeffs]
    w, h = signal.freqz(b, a)
    max_gain_unstable = max(abs(i) for i in h)
    z, p, k = signal.tf2zpk(b, a)
    new_p = []
    for i in p:
        if abs(i) > 1:
            i /= abs(i) ** 2
        i *= 0.9  # so peaks are not too sharp
        new_p.append(i)
    b, a = signal.zpk2tf(z, new_p, k)
    w, h = signal.freqz(b, a)
    max_gain_stable = max(abs(i) for i in h)
    z, p, k = signal.tf2zpk(b, a)
    k *= max_gain_unstable / max_gain_stable
    b, a = signal.zpk2tf(z, p, k)
    coeffs = a[1:]
    #----- tone vs noise -----#
    # residual
    RESIDUAL_SIZE = 4096 # we don't need entire residual, just a few cycles of lowest frequency
    coeffs.shape = (len(coeffs), 1)
    residual = actual[:RESIDUAL_SIZE] - past[:RESIDUAL_SIZE].dot(coeffs)
    residual = [float(i/b[0]) for i in residual]
    # autocorrelation
    freq_i = 60
    freq_f = 120
    shift_i = int(SAMPLE_RATE / freq_f)
    shift_f = int(SAMPLE_RATE / freq_i)
    max_ac = 0
    for shift in range(shift_i, shift_f):
        while shift >= len(residual):
            shift //= 2
        ac = autocorrelation(residual, shift)
        if ac > max_ac: max_ac = ac
    # energy
    energy = sum(i**2 for i in residual)
    power = energy / len(residual)
    # amplitudes
    tone = max_ac / energy
    tone_amp = math.sqrt(power * tone)
    noise_amp = math.sqrt(power * (1 - tone))
    if tone_amp / noise_amp > 2:
        tone_amp += noise_amp
        noise_amp = 0
    elif noise_amp / tone_amp > 2:
        noise_amp += tone_amp
        tone_amp = 0
    #----- outputs -----#
    return {
        'coeffs': [float(i) for i in coeffs],
        'tone_amp': float(b[0]) * tone_amp,
        'noise_amp': float(b[0]) * noise_amp,
    }

def analyze(x):
    ranges = stop_ranges(x)
    if ranges:
        i_i, i_f = ranges[0]
        duration = i_f - i_i
        i_step = duration // 4
        frames = []
        for i in range(
            i_i,
            i_f-i_step,
            i_step
        ):
            print(i, i+i_step)
            frames.append(parameterize(x[i:i+i_step]))
        return {
            'type': 'stop',
            'duration': duration,
            'frames': frames,
        }
    else:
        return parameterize(x)

#===== main =====#
phonetics = [
    'ae', 'ay', 'a', 'e', 'y', 'i', 'o', 'w', 'uu', 'u',
    'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z', 'm', 'n', 'ng', 'r', 'l',
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j', '0',
]
if args.plot_spectra:
    plot = dpc.Plot(
        transform=dpc.transforms.Grid(2100, 2000, 6),
        hide_axes=True,
    )
for i, phonetic in enumerate(phonetics):
    if args.only and phonetic != args.only:
        continue
    if args.start_from and i < phonetics.index(args.start_from):
        continue
    print(phonetic)
    if phonetic != '0':
        x = load(args.phonetics_file_path, (i * 10 + 4) * SAMPLE_RATE, 4 * SAMPLE_RATE)
    if args.plot_spectra:
        if phonetic == '0':
            continue
        from numpy.fft import fft
        plot.text(phonetic, **plot.transform(0, 0, 0, plot.series))
        plot.plot([float(abs(i)) for i in fft(x[:4096])[:2049]])
        continue
    if phonetic == '0':
        params = {
            'coeffs': [0.0] * args.order,
            'tone_amp': 0,
            'noise_amp': 0,
        }
    else:
        params = analyze(x)
    out_file_path = os.path.join(
        os.path.dirname(args.phonetics_file_path),
        phonetic + '.phonetic.json',
    )
    params = json.dumps(params, indent=2)
    print(params)
    with open(out_file_path, 'w') as file:
        file.write(params)
if args.plot_spectra:
    plot.show()
