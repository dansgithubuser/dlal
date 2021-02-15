#===== imports =====#
import dlal

from numpy.fft import fft
from scipy import signal

import argparse
import cmath
import copy
import json
import math
import os

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
parser.add_argument('--only', nargs='+')
parser.add_argument('--start-from')
parser.add_argument('--order', type=int, default=10)
parser.add_argument('--plot-stop-ranges', action='store_true')
parser.add_argument('--plot-spectra', action='store_true')
args = parser.parse_args()

#===== consts =====#
SAMPLE_RATE = 44100
FREQUENCY = 100  # of voice in args.phonetics_file_path
TONE_MARGIN = 0.15

#===== helpers =====#
def load(phonetics_file_path, start, duration):
    if not load.phonetics:
        load.phonetics = dlal.sound.read(phonetics_file_path).samples
    return load.phonetics[start:start+duration]
load.phonetics = None

def autocorrelation(x, shift):
    assert len(x) > shift
    return sum(i * j for i, j in zip(x[:-shift], x[shift:]))

def flabs(x):
    return float(abs(x))

def stop_ranges(x):
    window_size = 512
    silence_factor = 16
    # estimate power
    dx = [0] + [j - i for i, j in zip(x, x[1:])]  # speaker speed relates to energy; displacement does not
    envelope = [0] * window_size
    e = sum(i ** 2 for i in dx[:window_size])
    for i in range(len(dx) - window_size):
        envelope.append(e)
        e += dx[i + window_size] ** 2 - dx[i] ** 2
    # figure threshold
    sorted_envelope = sorted(envelope)
    threshold = sorted_envelope[len(envelope) // silence_factor]
    # if threshold is close to maximum, this isn't a stop
    maximum = sorted_envelope[-1]
    if threshold / maximum > 1 / silence_factor:
        return None
    # figure starts and stops
    rising_threshold = maximum / 64
    falling_threshold = maximum / 64
    approx_stop_duration = 2048
    result = []
    silent = True
    for i, v in enumerate(envelope[:-approx_stop_duration]):
        if silent:
            if v > rising_threshold:
                result.append([i])
                silent = False
        else:
            if v <  falling_threshold:
                start = result[-1][0]
                end = i + window_size
                result[-1].append((start + 3 * end) // 4)
                silent = True
    if len(result[-1]) == 1:
        result[-1].append(len(x)-1)
    # plot
    if args.plot_stop_ranges:
        plot = dpc.Plot()
        plot.plot(x)
        plot.plot(envelope)
        plot.line(0, rising_threshold, len(envelope), rising_threshold, r=255, g=0, b=0)
        plot.line(0, falling_threshold, len(envelope), falling_threshold, r=255, g=0, b=0)
        plot.line(0, threshold, len(envelope), threshold, r=0, g=0, b=255)
        for start, stop in result:
            plot.line(start, 0, stop, 0, r=0, g=255, b=0)
        plot.show()
    # done
    return result

def calc_n(x):
    n = 4096
    while n > len(x):
        n //= 2
    return n

def calc_spectrum(x, n):
    return [flabs(i) / math.sqrt(n) for i in fft(x[:n])[:n//2+1]]

class RunningMax:
    def __init__(self, initial, size=None):
        self.window = initial
        self.size = size or len(initial)
        self.value = max(initial)

    def add(self, value):
        self.value = max(self.value, value)
        self.window.append(value)
        if len(self.window) > self.size: self.pop()

    def pop(self):
        p = self.window.pop(0)
        if self.value == p:
            if not self.window:
                self.value = None
            else:
                self.value = max(self.window)

def calc_envelope(spectrum, freq_width):
    n = (len(spectrum) - 1) * 2
    width = freq_width * n // SAMPLE_RATE + 1
    envelope = []
    l_max = RunningMax([flabs(spectrum[0])], width//2)
    r_max = RunningMax([flabs(i) for i in spectrum[:width//2]])
    for i in range(len(spectrum)):
        envelope.append(max(flabs(spectrum[i]), min(l_max.value, r_max.value)))
        l_max.add(flabs(spectrum[i]))
        if i + width // 2 < len(spectrum):
            r_max.add(flabs(spectrum[i + width // 2]))
        else:
            r_max.pop()
    return envelope

def calc_tone_envelope(x):
    n = calc_n(x)
    spectrum = calc_spectrum(x, n)
    envelope = calc_envelope(spectrum, FREQUENCY * 2)  # span enough bins that we ignore harmonics
    return (n, spectrum, envelope)

def calc_toniness(x):
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
    # amplitudes
    energy = sum(i**2 for i in x)
    raw_tone = max_ac / energy
    tone = min(raw_tone, 1)
    if tone > (1 - TONE_MARGIN): tone = 1
    elif tone < TONE_MARGIN: tone = 0
    tone_amp = math.sqrt(tone)
    noise_amp = math.sqrt(1 - tone)
    # return
    return energy, raw_tone, tone_amp, noise_amp

def parameterize(x):
    #----- tone vs noise -----#
    energy, tone, tone_amp, noise_amp = calc_toniness(x)
    #----- find formants -----#
    n, spectrum, envelope = calc_tone_envelope(x)
    tone_formants = IirBank.fitting_envelope(envelope, 0.005)
    tone_formants.multiply(tone_amp)
    #----- calculate noise filter -----#
    tone_spectrum = tone_formants.spectrum(n)
    noise_spectrum = [
        math.sqrt(max(0, spectrum[i] ** 2 - tone_spectrum[i] ** 2))
        for i in range(len(envelope))
    ]
    noise_envelope = calc_envelope(noise_spectrum, 400)
    noise_formants = IirBank.fitting_envelope(noise_envelope, 0.02)
    noise_formants.multiply(noise_amp)
    #----- outputs -----#
    result = {}
    if tone_amp: result['tone_formants'] = tone_formants.formants
    if noise_amp: result['noise_formants'] = noise_formants.formants
    result['meta'] = {
        'energy': energy,
        'tone': tone,
        'tone_transfer': tone_formants.energy_transfer(n),
        'noise_transfer': noise_formants.energy_transfer(n),
    }
    return result

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

def analyze(x=None):
    if x == None:
        return {
            'type': 'continuant',
            'frames': [{}],
        }
    cuts = cut_phonetic(x)
    if len(cuts) == 1:
        frames = [parameterize(cuts[0])]
        return {
            'type': 'continuant',
            'frames': frames,
            'meta': {
                'energy': frames[0]['meta']['energy'],
                'tone': frames[0]['meta']['tone'],
                'voiced': frames[0]['meta']['tone'] > TONE_MARGIN,
            },
        }
    else:
        energy, tone, _, _ = calc_toniness(sum(cuts, []))
        frames = []
        for i, cut in enumerate(cuts):
            frames.append(parameterize(cut))
        return {
            'type': 'stop',
            'duration': sum(len(cut) for cut in cuts),
            'frames': frames,
            'meta': {
                'energy': energy,
                'tone': tone,
                'voiced': tone > TONE_MARGIN,
            },
        }

class IirBank:
    def fitting_envelope(envelope, width):
        visited = [False] * len(envelope)
        iir_bank = IirBank()
        for i in range(args.order):
            # find unvisited formant with biggest delta from spectrum
            spectrum = iir_bank.spectrum((len(envelope)-1) * 2)
            delta = [i - j for i, j in zip(envelope, spectrum)]
            unvisited = [i for i, j in zip(delta, visited) if not j]
            if not unvisited:
                iir_bank.formants.append({
                    'freq': SAMPLE_RATE / 4,
                    'amp': 0,
                    'width': width,
                })
                continue
            peak = max(unvisited)
            peak_i = delta.index(peak)
            # visit right
            peak_r = peak_i
            while peak_r+1 < len(envelope):
                visited[peak_r] = True
                if envelope[peak_r] < envelope[peak_r+1]:
                    break
                peak_r += 1
            # visit left
            peak_l = peak_i
            while peak_l-1 >= 0:
                visited[peak_l] = True
                if envelope[peak_l] < envelope[peak_l-1]:
                    break
                peak_l -= 1
            # find freq based on centroid
            centroid = sum(i * envelope[i] for i in range(peak_l, peak_r+1)) / sum(v for v in envelope[peak_l:peak_r+1])
            freq = centroid / ((len(envelope) - 1) * 2) * SAMPLE_RATE
            # append formant
            iir_bank.formants.append({
                'freq': freq,
                'amp': peak,
                'width': width,
            })
            # widening
            e = iir_bank.error(envelope)
            widened = copy.deepcopy(iir_bank)
            widened.formants[-1]['width'] *= 2
            for i in range(8):
                e_w = widened.error(envelope)
                if e_w >= e: break
                e = e_w
                iir_bank = widened
        # sort by frequency
        iir_bank.formants = sorted(iir_bank.formants, key=lambda i: i['freq'])
        return iir_bank

    def __init__(self, formants=[]):
        self.formants = copy.copy(formants)

    def spectrum(self, n):
        spectrum = [0]*(n // 2 + 1)
        for iir in self.formants:
            w = iir['freq'] / SAMPLE_RATE * 2*math.pi
            p = cmath.rect(1.0 - iir['width'], w);
            z_w = cmath.rect(1.0, w);
            gain = iir['amp'] * abs((z_w - p) * (z_w - p.conjugate()));
            b, a = signal.zpk2tf([], [p, p.conjugate()], gain)
            w, h = signal.freqz(b, a, n // 2 + 1, include_nyquist=True)
            for i in range(len(spectrum)):
                spectrum[i] += h[i]
        return [flabs(i) for i in spectrum]

    def plot_spectrum(self, n, plot):
        plot.plot([math.log(i) for i in self.spectrum(n)])

    def energy_transfer(self, n):
        return sum(i ** 2 for i in self.spectrum(n)) / n

    def multiply(self, f):
        for formant in self.formants:
            formant['amp'] *= f

    def error(self, envelope):
        s = self.spectrum((len(envelope)-1) * 2)
        return sum(abs(flabs(i) - j) for i, j in zip(s, envelope))

#===== main =====#
phonetics = [
    'ae', 'ay', 'a', 'e', 'y', 'i', 'o', 'w', 'uu', 'u',
    'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z', 'm', 'n', 'ng', 'r', 'l',
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j', '0',
]
if args.plot_spectra:
    grid_w = 8
    if args.only:
        grid_w = 1
    plot = dpc.Plot(
        transform=dpc.transforms.Compound(
            dpc.transforms.Grid(4200, 10, grid_w),
            (dpc.transforms.Default('bcyg'), 4),
        ),
        primitive=dpc.primitives.Line(),
        hide_axes=True,
    )
for i, phonetic in enumerate(phonetics):
    if args.only and phonetic not in args.only:
        continue
    if args.start_from and i < phonetics.index(args.start_from):
        continue
    out_file_path = os.path.join(
        os.path.dirname(args.phonetics_file_path),
        phonetic + '.phonetic.json',
    )
    if args.plot_spectra:
        if phonetic == '0': continue
        x = load(args.phonetics_file_path, (i * 10 + 4) * SAMPLE_RATE, 4 * SAMPLE_RATE)
        cuts = cut_phonetic(x)
        if len(cuts) > 1:
            cuts.insert(0, x)
        with open(out_file_path) as file:
            params = json.loads(file.read())
        for frame_i, frame in enumerate(params['frames']):
            n, spectrum, envelope = calc_tone_envelope(cuts[frame_i])
            t = plot.transform(-20, 0, 0, plot.series)
            t.update({'r': 255, 'g': 0, 'b': 255})
            plot.text(phonetic + str(frame_i), **t)
            plot.plot([math.log(i) for i in spectrum])
            plot.plot([math.log(i) for i in envelope])
            if 'tone_formants' in frame and (len(cuts) == 1 or frame_i):
                IirBank(frame['tone_formants']).plot_spectrum(n, plot)
            else:
                plot.next_series()
            if 'noise_formants' in frame and (len(cuts) == 1 or frame_i):
                IirBank(frame['noise_formants']).plot_spectrum(n, plot)
            else:
                plot.next_series()
    else:
        print(phonetic)
        if phonetic == '0':
            params = analyze()
        else:
            x = load(args.phonetics_file_path, (i * 10 + 4) * SAMPLE_RATE, 4 * SAMPLE_RATE)
            params = analyze(x)
        params = json.dumps(params, indent=2)
        with open(out_file_path, 'w') as file:
            file.write(params)
if args.plot_spectra:
    plot.show()
