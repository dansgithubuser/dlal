#===== imports =====#
import dlal

import numpy as np
from numpy.fft import fft
from scipy import signal

import argparse
import cmath
import copy
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
parser.add_argument('--plot-stop-ranges', action='store_true')
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
    envelope = []
    maximum = None
    for i in range(window_size, len(x)):
        if maximum == None:
            maximum = max(x[i-window_size:i+1])
        else:
            maximum = max(maximum, x[i])
        envelope.append(maximum)
        if maximum == x[i-window_size]:
            maximum = None
    # figure threshold
    sorted_envelope = sorted(envelope)
    threshold = sorted_envelope[len(envelope) // silence_factor]
    # if threshold is close to maximum, this isn't a stop
    maximum = sorted_envelope[-1]
    if threshold / maximum > 1 / silence_factor:
        return None
    # figure starts and stops
    result = []
    silent = True
    for i, v in enumerate(envelope):
        if silent:
            if v > maximum * 1/4:
                result.append([i])
                silent = False
        else:
            if v < maximum * 1/8:
                result[-1].append(i + window_size)
                silent = True
    if len(result[-1]) == 1:
        result[-1].append(len(x)-1)
    # plot
    if args.plot_stop_ranges:
        plot = dpc.Plot()
        plot.plot(x)
        plot.plot(envelope)
        plot.line(0, maximum * 1/4, len(envelope), maximum * 1/4, r=255, g=0, b=0)
        plot.line(0, maximum * 1/8, len(envelope), maximum * 1/8, r=255, g=0, b=0)
        plot.line(0, threshold, len(envelope), threshold, r=0, g=0, b=255)
        for start, stop in result:
            plot.line(start, 0, stop, 0, r=0, g=255, b=0)
        plot.show()
    # done
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

class Filter:
    def __init__(self, p, z, k, n, envelope=None):
        self.p = p
        self.z = z
        self.k = k
        self.n = n
        self.envelope = envelope

    def all_p(self):
        return self.p + [i.conjugate() for i in self.p]

    def all_z(self):
        return self.z + [i.conjugate() for i in self.z]

    def calc_error(self):
        w, h = self.spectrum()
        return sum(
            (abs(h_i) - envelope_i.amp) ** 2
            for h_i, envelope_i
            in zip(h, self.envelope)
        )

    def mutate(self, heat, max_pole_abs):
        r = random.randint(0, 100)
        if r < 80:
            # move each pole toward unit circle or origin, increase or decrease gain
            def mutate_one(i):
                ret = i * abs(i) ** random.uniform(-0.5, 0.5)
                if abs(ret) >= max_pole_abs:
                    ret = i
                return ret
            k = self.k * random.uniform(0.5, 2) ** heat
            if k == 0:
                k = self.k
            return Filter(
                [mutate_one(i) for i in self.p],
                self.z,
                k,
                self.n,
                self.envelope,
            )
        else:
            # alter frequency of a zero
            i = random.randint(0, len(self.z)-1)
            phase = cmath.phase(self.z[i])
            if random.randint(0, 1):
                if i == len(self.z)-1:
                    p = math.pi
                else:
                    p = cmath.phase(self.p[i+1])
            else:
                p = cmath.phase(self.p[i])
            t = random.uniform(0, heat)
            phase = phase * (1-t) + p * t
            z = copy.copy(self.z)
            z[i] = cmath.rect(abs(z[i]), phase)
            return Filter(self.p, z, self.k, self.n, self.envelope)

    def tf(self):
        return signal.zpk2tf(self.all_z(), self.all_p(), self.k)

    def spectrum(self):
        b, a = self.tf()
        return signal.freqz(b, a, self.n//2+1, include_nyquist=True)

    def h_max(self):
        w, h = self.spectrum()
        return max(float(abs(i)) for i in h)

    def energy(self):
        w, h = self.spectrum()
        return sum((abs(i)/len(h))**2 for i in h)

    def plot(self, log=False, bottom=None, plot=None):
        w, h = self.spectrum()
        if plot == None:
            plot = dpc.Plot(primitive=dpc.primitives.Line())
        if log:
            f = lambda x: 20 * math.log10(x)
        else:
            f = lambda x: x
        y = [f(float(abs(i))) for i in h]
        if bottom:
            y = [max(bottom, i) for i in y]
        for i in self.p:
            x = cmath.phase(i) / (2*math.pi) * self.n
            xyi = plot.transform(x,  0, 0, plot.series)
            xyf = plot.transform(x, 10, 0, plot.series)
            plot.line(xyi['x'], xyi['y'], xyf['x'], xyf['y'], r=0, g=255, b=0)
        for i in self.z:
            x = cmath.phase(i) / (2*math.pi) * self.n
            xyi = plot.transform(x,  0, 0, plot.series)
            xyf = plot.transform(x, 10, 0, plot.series)
            plot.line(xyi['x'], xyi['y'], xyf['x'], xyf['y'], r=255, g=0, b=0)
        plot.plot(y)
        if self.envelope:
            plot.plot([f(i.amp) for i in self.envelope])
        return plot

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
    BRANCHES = (1 << args.order) * 5
    MAX_POLE_ABS = 0.99
    # init
    p = sorted([
        cmath.rect(min(0.9 * MAX_POLE_ABS, 1 - 1 / max(amp, 2)), freq)
        for freq, amp in formants.items()
    ], key=cmath.phase)
    if any(i.imag < 0 for i in p) or any(abs(i) > MAX_POLE_ABS for i in p):
        raise Exception('improper initial pole')
    z = [  # cmath.phase(p[i]) < cmath.phase(z[i]) < cmath.phase(p[i+1])
        cmath.rect(1, (cmath.phase(p[i]) + cmath.phase(p[i+1])) / 2)
        for i in range(len(p) - 1)
    ]
    z.append(cmath.rect(
        abs(p[-1]),
        (cmath.phase(p[-1]) + math.pi) / 2,
    ))
    fil = Filter(p, z, 1, n, envelope)
    e = fil.calc_error()
    heat = HEAT
    # loop
    for i in range(STEPS):
        fil_tries = [fil]+[fil.mutate(heat, MAX_POLE_ABS) for i in range(BRANCHES)]
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
    # autocorrelation
    freq_i = 60
    freq_f = 120
    shift_i = int(SAMPLE_RATE / freq_f)
    shift_f = int(SAMPLE_RATE / freq_i)
    max_ac = 0
    min_ac_samples = 128
    for shift in range(shift_i, shift_f):
        ac_samples = len(x) - shift
        if ac_samples <= min_ac_samples:
            break
        ac = abs(autocorrelation(x, shift))
        ac_power = ac / ac_samples
        ac = ac_power * len(x)  # for fair comparison w energy
        if ac > max_ac:
            max_ac = ac
    # energy
    energy = sum(i**2 for i in x)
    power = energy / len(x)
    # amplitudes
    tone = min(max_ac / energy, 1)
    tone_amp = math.sqrt(power * tone)
    noise_amp = math.sqrt(power * (1 - tone))
    #----- outputs -----#
    return {
        'poles': [json_complex(i.real, i.imag) for i in fil.p],
        'zeros': [json_complex(i.real, i.imag) for i in fil.z],
        'gain': fil.k,
        'tone_amp': tone_amp,
        'noise_amp': noise_amp,
    }

def cut_stop(x):
    step = len(x) // int(len(x) / 512)
    return [x[i:i+step] for i in range(0, len(x)-step, step)]

def cut_phonetic(x):
    ranges = stop_ranges(x)
    if ranges:
        i_i, i_f = ranges[0]
        return cut_stop(x[i_i:i_f])
    else:
        return [x]

def analyze(x):
    cuts = cut_phonetic(x)
    if len(cuts) == 1:
        return parameterize(cuts[0])
    else:
        return {
            'type': 'stop',
            'duration': sum(len(cut) for cut in cuts),
            'frames': [parameterize(cut) for cut in cuts],
        }

#===== main =====#
phonetics = [
    'ae', 'ay', 'a', 'e', 'y', 'i', 'o', 'w', 'uu', 'u',
    'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z', 'm', 'n', 'ng', 'r', 'l',
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j', '0',
]
if args.plot_spectra:
    plot = dpc.Plot(
        transform=dpc.transforms.Compound(
            dpc.transforms.Grid(300, 60, 8),
            (dpc.transforms.Default(), 2),
        ),
        primitive=dpc.primitives.Line(),
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
        asset_path = f'assets/phonetics/{phonetic}.phonetic.json'
        if os.path.exists(asset_path):
            with open(asset_path) as f:
                asset = json.loads(f.read())
            asset_iter = iter(asset.get('frames', [asset]))
        else:
            asset_iter = None
        cuts = cut_phonetic(x)
        for j, cut in enumerate(cuts):
            name = phonetic
            if len(cuts) != 1:
                name += str(j)
            t = plot.transform(-20, 0, 0, plot.series)
            t.update({'r': 255, 'g': 0, 'b': 255})
            plot.text(name, **t)
            xf = fft(cut[:512])
            xf = [math.log(float(abs(i))) for i in xf[:len(xf)//2+1]]
            xf = [i for i in xf]
            plot.plot(xf)
            if asset_iter:
                asset_frame = next(asset_iter)
                poles = asset_frame['poles']
                poles = [i['re'] + 1j * i['im'] for i in poles]
                zeros = asset_frame['zeros']
                zeros = [i['re'] + 1j * i['im'] for i in zeros]
                gain = asset_frame['gain']
                Filter(poles, zeros, gain, 512).plot(log=True, bottom=-10, plot=plot)
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
