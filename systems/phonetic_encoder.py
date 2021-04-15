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

#===== helpers =====#
def load(phonetics_file_path, start, duration):
    if not load.phonetics:
        load.phonetics = dlal.sound.read(phonetics_file_path).samples
    return load.phonetics[start:start+duration]
load.phonetics = None

def autocorrelation(x, shift):
    assert len(x) > shift
    return sum(abs(i * j) for i, j in zip(x[:-shift], x[shift:]))

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
    falling_threshold = maximum / 256
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
                result[-1].append(min(end, start + int(0.04 * SAMPLE_RATE)))
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
    n = 1 << 12
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
    mx = RunningMax([flabs(i) for i in spectrum[:width//2]], width)
    for i in range(len(spectrum)):
        envelope.append(mx.value)
        if i + width // 2 < len(spectrum):
            mx.add(flabs(spectrum[i + width // 2]))
        else:
            mx.pop()
    return envelope

def calc_tone_envelope(x):
    n = calc_n(x)
    spectrum = calc_spectrum(x, n)
    envelope = calc_envelope(spectrum, FREQUENCY)  # span enough bins that we ignore harmonics
    return (n, spectrum, envelope)

class RunningAvg:
    def __init__(self, initial, size=None):
        self.window = initial
        self.size = size or len(initial)
        self.sum = sum(initial)

    def add(self, value):
        self.window.append(value)
        if len(self.window) > self.size:
            self.sum -= self.window.pop(0)
        self.sum += value

    def pop(self):
        self.sum -= self.window.pop(0)

    def value(self):
        return self.sum / len(self.window)

def calc_toniness(x):
    energy = sum(i**2 for i in x)
    # remove low frequencies
    y = []
    avg = RunningAvg(x[:512], 1024)
    for i in range(len(x)):
        y.append(x[i] - avg.value())
        if i + avg.size // 2 < len(x):
            avg.add(x[i + avg.size // 2])
        else:
            avg.pop()
    x = y
    # autocorrelation
    min_ac_samples = 128
    freq_i = 60
    freq_f = 120
    shift_i = int(SAMPLE_RATE / freq_f)
    shift_f = int(SAMPLE_RATE / freq_i)
    acs = []
    for shift in range(shift_i, shift_f):
        ac_samples = len(x) - shift
        if ac_samples <= min_ac_samples:
            break
        ac = autocorrelation(x, shift)
        ac_power = ac / ac_samples
        ac = ac_power * len(x)  # for fair comparison w energy
        acs.append(ac)
    max_ac = max(acs)
    min_ac = min(acs)
    chaos = sum(((i - j) / (max_ac - min_ac)) ** 2 for i, j in zip(acs, acs[1:])) / len(acs)
    # amplitudes
    raw_tone = max_ac / energy
    tone = min(raw_tone, 1)
    if tone > 0.8: tone = 1
    elif chaos > 0.001: tone = 0
    tone_amp = tone and 1
    noise_amp = math.sqrt(1 - tone)
    # return
    return {
        'energy': energy,
        'tone': raw_tone,
        'tone_amp': tone_amp,
        'noise_amp': noise_amp,
        'chaos': chaos,
        'voiced': tone != 0,
    }

def parameterize(x, toniness=None):
    #----- tone vs noise -----#
    if toniness == None:
        toniness = calc_toniness(x)
    #----- find formants -----#
    n, spectrum, envelope = calc_tone_envelope(x)
    tone_formants = IirBank.fitting_envelope(
        envelope,
        0.01,
        False,
        [
            [
                200 + (i+0) ** 2 * 5000 // args.order ** 2,
                700 + (i+1) ** 2 * 5000 // args.order ** 2,
            ]
            for i in range(args.order)
        ],
    )
    tone_formants.multiply(toniness['tone_amp'])
    #----- calculate noise filter -----#
    tone_spectrum = tone_formants.spectrum(n)
    noise_spectrum = [
        math.sqrt(max(0, spectrum[i] ** 2 - tone_spectrum[i] ** 2))
        for i in range(len(envelope))
    ]
    noise_envelope = calc_envelope(noise_spectrum, 400)
    noise_formants = IirBank.fitting_envelope(
        noise_envelope,
        0.001,
        True,
        [
            [
                (i+0) * 20000 // args.order,
                (i+1) * 20000 // args.order,
            ]
            for i in range(args.order)
        ],
        1,
    )
    noise_formants.multiply(toniness['noise_amp'])
    #----- normalize -----#
    transfer = math.sqrt(tone_formants.energy_transfer(n) + noise_formants.energy_transfer(n))
    for formant in tone_formants.formants + noise_formants.formants:
        formant['amp'] /= transfer
    #----- outputs -----#
    result = {}
    if toniness['tone_amp']: result['tone_formants'] = tone_formants.formants
    if toniness['noise_amp']: result['noise_formants'] = noise_formants.formants
    result['meta'] = {
        'toniness': toniness,
        'tone_transfer': tone_formants.energy_transfer(n),
        'noise_transfer': noise_formants.energy_transfer(n),
    }
    return result

def cut_stop(x):
    step = 512
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
            'voiced': False,
            'frames': [{}],
        }
    cuts = cut_phonetic(x)
    if len(cuts) == 1:
        frames = [parameterize(cuts[0])]
        return {
            'type': 'continuant',
            'voiced': frames[0]['meta']['toniness']['voiced'],
            'frames': frames,
            'meta': frames[0]['meta'],
        }
    else:
        toniness = calc_toniness(sum(cuts, []))
        frames = []
        for i, cut in enumerate(cuts):
            frames.append(parameterize(cut, toniness=toniness))
        unvoiced_stop_silence = 0
        if not toniness['voiced']:
            unvoiced_stop_silence = SAMPLE_RATE * 60 // 1000
            for i in range(0, unvoiced_stop_silence, len(cut)):
                frames.insert(0, {})
        return {
            'type': 'stop',
            'voiced': toniness['voiced'],
            'duration': sum(len(cut) for cut in cuts) + unvoiced_stop_silence,
            'frames': frames,
            'meta': {
                'toniness': toniness,
            },
        }

def get_glottal_sound(x):
    n, spectrum, envelope = calc_tone_envelope(x)
    bank = IirBank.fitting_envelope(
        envelope,
        0.01,
        False,
        [
            [
                200 + (i+0) ** 2 * 16000 // 40 ** 2,
                700 + (i+1) ** 2 * 16000 // 40 ** 2,
            ]
            for i in range(40)
        ],
        order=40
    )
    for formant in bank.formants:
        formant['amp'] = 1 / formant['amp'] if formant['amp'] else 0
    y = bank.filter(x)
    y_max = max(abs(i) for i in y)
    y = [i / y_max for i in y]
    return y

class IirBank:
    def fitting_envelope(envelope, width, widen, formant_ranges, pole_pairs=2, order=args.order):
        visited = [False] * len(envelope)
        iir_bank = IirBank()
        def append_formant(freq, amp):
            iir_bank.formants.append({
                'freq': freq,
                'amp': amp,
                'width': width,
                'order': 2 * pole_pairs,
            })
        for i in range(order):
            # find unvisited formant with biggest delta from spectrum
            spectrum = iir_bank.spectrum((len(envelope)-1) * 2)
            delta = [i - j for i, j in zip(envelope, spectrum)]
            for j in range(len(delta)):
                if not formant_ranges[i][0] <= j / ((len(envelope) - 1) * 2) * SAMPLE_RATE <= formant_ranges[i][1]:
                    delta[j] = 0
            unvisited = [i for i, j in zip(delta, visited) if not j]
            if not unvisited:
                append_formant(sum(formant_ranges[i]) / 2, 0)
                continue
            peak = max(unvisited)
            if peak <= 0:
                append_formant(sum(formant_ranges[i]) / 2, 0)
                continue
            # find index
            peak_i = delta.index(peak)
            peak_j = peak_i
            while peak_j+1 < len(delta) and delta[peak_j+1] == delta[peak_i]:
                peak_j += 1
            peak_i = (peak_i + peak_j) // 2
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
            w = min(peak_r - peak_i, peak_i - peak_l)
            l = peak_i - w
            r = peak_i + w + 1
            centroid = sum(i * envelope[i] for i in range(l, r)) / sum(v for v in envelope[l:r])
            freq = centroid / ((len(envelope) - 1) * 2) * SAMPLE_RATE
            # append formant
            append_formant(freq, peak)
            # widening
            if widen:
                e = iir_bank.formant_error(envelope, formant_ranges[i])
                widened = copy.deepcopy(iir_bank)
                for _ in range(8):
                    widened.formants[-1]['width'] *= 2
                    e_w = widened.formant_error(envelope, formant_ranges[i])
                    if e_w >= e: break
                    e = e_w
                    iir_bank = widened
        # sort by frequency
        iir_bank.formants = sorted(iir_bank.formants, key=lambda i: i['freq'])
        return iir_bank

    def __init__(self, formants=[]):
        self.formants = copy.copy(formants)

    def get_tf(self, formant):
        w = formant['freq'] / SAMPLE_RATE * 2*math.pi
        p = cmath.rect(1.0 - formant['width'], w);
        z_w = cmath.rect(1.0, w);
        gain = formant['amp'] * abs((z_w - p) * (z_w - p.conjugate())) ** (formant['order'] // 2);
        return signal.zpk2tf([], [p, p.conjugate()] * (formant['order'] // 2), gain)

    def spectrum(self, n):
        spectrum = [0]*(n // 2 + 1)
        for formant in self.formants:
            b, a = self.get_tf(formant)
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

    def formant_error(self, envelope, formant_range):
        spectrum = self.spectrum((len(envelope)-1) * 2)
        start, end = [i / (SAMPLE_RATE/2) * (len(spectrum)-1) for i in formant_range]
        err = 0
        for i, (spec, env) in enumerate(zip(spectrum, envelope)):
            e = flabs(spec) - env
            if i <= end:
                # we are in existing formant range, error is bad, going over is very bad
                if e > 0:
                    err += 4 * e
                else:
                    err += abs(e)
            else:
                # we are in a future formant range, error is fine, going over is very bad
                if e > 0:
                    err += 4 * e
        return err

    def filter(self, x):
        y = [0] * len(x)
        for formant in self.formants:
            b, a = self.get_tf(formant)
            y = [
                float(i.real) + j
                for i, j in zip(signal.lfilter(b, a, x), y)
            ]
        return y

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
        for frame_i, frame in enumerate([i for i in params['frames'] if i]):
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
        if phonetic == 'a':
            dlal.sound.Sound(get_glottal_sound(x), SAMPLE_RATE).to_flac(os.path.join(
                os.path.dirname(args.phonetics_file_path),
                'glottis.flac',
            ))
if args.plot_spectra:
    plot.show()
