#===== imports =====#
import dlal

from numpy.fft import fft
from scipy import signal

import argparse
import cmath
import json
import math
import os
import random
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
parser.add_argument('--order', type=int, default=5)
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

# plot spectrum of sampled signal
def plot_sample_spectrum(plot, x):
    if plot == None:
        plot = dpc.Plot()
    f = fft(x)
    plot.plot([
        float(abs(i))
        for i in f[:len(f) // 2 + 1]
    ])
    return plot

# plot spectrum of filter(b, a)
def plot_filter_spectrum(plot, b, a):
    if plot == None:
        plot = dpc.Plot()
    w, h = signal.freqz(b, a)
    plot.plot([float(abs(i)) for i in h])
    return plot

# plot poles and zeros of filter(z, p)
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

def json_complex(re, im):
    return {'re': re, 'im': im}

def parameterize(x):
    #----- find formants -----#
    # parameters
    FREQUENCY = 100
    # consts
    n = 1 << 12
    while n > len(x):
        n >>= 1
    spectrum = fft(x[:n])[:n//2+1]
    # calculate envelope
    width = FREQUENCY * n // SAMPLE_RATE + 1  # span enough bins that we ignore harmonics
    envelope = []
    for i in range(len(spectrum)):
        j_i = i - width // 2
        j_f = j_i + width
        if j_i < 0:
            j_i = 0
        if j_f > len(spectrum):
            j_f = len(spectrum)
        amp = 0
        for j in range(j_i, j_f):
            amp = max(amp, float(abs(spectrum[j])))
        envelope.append(amp)
    # calculate frequency of formants
    class Amp:
        def __init__(self, amp):
            self.amp = amp
            self.visited = False

    envelope = [Amp(i) for i in envelope]
    formants = {}
    for i in range(args.order):
        # find center of max unvisited formant
        peak_amp = max([i.amp for i in envelope if not i.visited])
        peak_i = [i.amp for i in envelope].index(peak_amp)
        peak_f = peak_i
        while peak_f+1 < len(envelope) and envelope[peak_f+1].amp == peak_amp:
            peak_f += 1
        freq = (peak_i + peak_f) / 2 / n * 2 * math.pi
        formants[freq] = peak_amp
        # visit right
        i = peak_i
        while i+1 < len(envelope):
            envelope[i].visited = True
            if envelope[i].amp < envelope[i+1].amp:
                break
            i += 1
        # visit left
        i = peak_i
        while i-1 >= 0:
            envelope[i].visited = True
            if envelope[i].amp < envelope[i-1].amp:
                break
            i -= 1
    #----- gradient descent poles to match spectrum -----#
    STEPS = 10
    HEAT = 1
    ANNEALING_MULTIPLIER = 0.9
    BRANCHES = 1 << args.order
    MAX_POLE_ABS = 0.99
    # helpers
    class Filter:
        def __init__(self, p, z, k):
            self.p = p
            self.z = z
            self.k = k

        def all_p(self):
            return self.p + [i.conjugate() for i in self.p]

        def all_z(self):
            return self.z + [i.conjugate() for i in self.z]

        def calc_error(self):
            w, h = self.spectrum()
            return sum((abs(h_i) - envelope_i.amp) ** 2 for h_i, envelope_i in zip(h, envelope))

        # move each pole toward unit circle or origin, increase or decrease gain
        def mutate(self, heat):
            def mutate_one(i):
                ret = i * abs(i) ** random.uniform(-0.5, 0.5)
                if abs(ret) >= MAX_POLE_ABS:
                    ret = i
                return ret
            k = self.k * random.uniform(0.5, 2) ** heat
            if k == 0:
                k = self.k
            return Filter(
                [mutate_one(i) for i in self.p],
                self.z,
                k,
            )

        def tf(self):
            return signal.zpk2tf(self.all_z(), self.all_p(), self.k)

        def spectrum(self):
            b, a = self.tf()
            return signal.freqz(b, a, n//2+1, include_nyquist=True)

        def h_max(self):
            w, h = self.spectrum()
            return max(float(abs(i)) for i in h)

        def energy(self):
            w, h = self.spectrum()
            return sum((abs(i)/len(h))**2 for i in h)

        def plot(self, log=False):
            w, h = self.spectrum()
            plot = dpc.Plot(primitive=dpc.primitives.Line())
            if log:
                f = lambda x: 20 * math.log10(x)
            else:
                f = lambda x: x
            plot.plot([f(float(abs(i))) for i in h])
            plot.plot([f(i.amp) for i in envelope])
            for i in self.p:
                x = cmath.phase(i) / (2*math.pi) * n
                plot.line(x, 0, x, 100, r=0, g=0, b=255)
            plot.show()

    # init
    p = sorted([
        cmath.rect(min(0.9 * MAX_POLE_ABS, 1 - 1 / max(amp, 2)), freq)
        for freq, amp in formants.items()
    ], key=cmath.phase)
    if any(i.imag < 0 for i in p) or any(abs(i) > MAX_POLE_ABS for i in p):
        raise Exception('improper initial pole')
    z = [
        cmath.rect(1, (cmath.phase(p[i]) + cmath.phase(p[i+1])) / 2)
        for i in range(len(p) - 1)
    ]
    z.append(cmath.rect(
        abs(p[-1]),
        (cmath.phase(p[-1]) + math.pi) / 2,
    ))
    fil = Filter(p, z, 1)
    e = fil.calc_error()
    heat = HEAT
    # loop
    for i in range(STEPS):
        fil_tries = [fil]+[fil.mutate(heat) for i in range(BRANCHES)]
        e_tries = [i.calc_error() for i in fil_tries]
        i = e_tries.index(min(e_tries))
        fil = fil_tries[i]
        e = e_tries[i]
        heat *= ANNEALING_MULTIPLIER
    if any(i.imag < 0 for i in fil.p) or any(abs(i) > MAX_POLE_ABS for i in fil.p):
        raise Exception('improper final pole')
    # normalize
    fil.k /= math.sqrt(fil.energy())
    #----- tone vs noise -----#
    x = x[:4096]  # we don't need entire signal, just a few cycles of lowest frequency
    # autocorrelation
    freq_i = 60
    freq_f = 120
    shift_i = int(SAMPLE_RATE / freq_f)
    shift_f = int(SAMPLE_RATE / freq_i)
    max_ac = 0
    for shift in range(shift_i, shift_f):
        while shift >= len(x):
            shift //= 2
        ac = autocorrelation(x, shift)
        if ac > max_ac: max_ac = ac
    # energy
    energy = sum(i**2 for i in x)
    power = energy / len(x)
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
        'poles': [json_complex(i.real, i.imag) for i in fil.p],
        'zeros': [json_complex(i.real, i.imag) for i in fil.z],
        'gain': fil.k,
        'tone_amp': tone_amp,
        'noise_amp': noise_amp,
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
        plot.text(phonetic, **plot.transform(0, 0, 0, plot.series))
        plot.plot([float(abs(i)) for i in fft(x[:4096])[:2049]])
        continue
    if phonetic == '0':
        params = {
            'poles': [json_complex(0, 0)] * args.order,
            'zeros': [json_complex(0, 0)] * args.order,
            'gain': 0,
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
