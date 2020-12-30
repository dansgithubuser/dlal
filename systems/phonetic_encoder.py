#===== imports =====#
import dlal

from numpy.fft import fft

import argparse
import cmath
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
parser.add_argument('--order', type=int, default=5)
parser.add_argument('--plot-stop-ranges', action='store_true')
parser.add_argument('--plot-spectra', action='store_true')
args = parser.parse_args()

#===== consts =====#
SAMPLE_RATE = 44100
FREQUENCY = 100  # of voice in args.phonetics_file_path

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

def calc_n(x):
    n = 4096
    while n > len(x):
        n //= 2
    return n

def calc_envelope(x, n):
    spectrum = fft(x[:n])[:n//2+1]
    width = FREQUENCY * n // SAMPLE_RATE + 1  # span enough bins that we ignore harmonics
    avg = sum(float(abs(i)) for i in spectrum) / len(spectrum)
    dev = math.sqrt(sum((float(abs(i)) - avg) ** 2 for i in spectrum))
    dev_n = dev / len(spectrum)
    threshold = 0.1
    if dev_n < threshold:
        # if this is a wide spectrum, make sure width is extra wide so we don't cluster formants
        width = int(width * 0.1 / dev_n)
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
        envelope.append(amp / math.sqrt(n))
    return envelope

def parameterize(x=None):
    if x:
        #----- find formants -----#
        # consts
        n = calc_n(x)
        envelope = calc_envelope(x, n)
        # calculate frequency of formants
        class Amp:
            def __init__(self, amp):
                self.amp = amp
                self.visited = False

        envelope = [Amp(i) for i in envelope]
        formants = []
        for i in range(args.order):
            # find center of max unvisited formant
            peak_amp = max([i.amp for i in envelope if not i.visited])
            peak_i = [i.amp for i in envelope].index(peak_amp)
            peak_f = peak_i
            while peak_f+1 < len(envelope) and envelope[peak_f+1].amp == peak_amp:
                peak_f += 1
            freq = (peak_i + peak_f) / 2 / n * SAMPLE_RATE
            formants.append({
                'freq': freq,
                'amp': peak_amp,
                'width': 0.01,
            })
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
        formants = sorted(formants, key=lambda i: i['freq'])
        # widen formants until filter has same energy as signal
        energy = sum(i**2 for i in x[:n])
        while formants[0]['width'] < 0.5:
            e = energy_transfer(formants, n)
            if math.sqrt(2) * e >= energy:
                break
            for formant in formants:
                formant['width'] *= 2
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
        # amplitudes
        energy = sum(i**2 for i in x)
        tone = min(max_ac / energy, 1)
        tone_amp = math.sqrt(tone)
        noise_amp = math.sqrt(1 - tone)
        #----- outputs -----#
        return {
            'formants': formants,
            'tone_amp': tone_amp,
            'noise_amp': noise_amp,
        }
    else:
        return {
            'formants': [
                {
                    'freq': 0,
                    'amp': 0,
                }
                for i in range(args.order)
            ],
            'tone_amp': 0,
            'noise_amp': 0,
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

def analyze(x=None):
    if x == None:
        return {
            'type': 'continuant',
            'frames': [parameterize()],
        }
    cuts = cut_phonetic(x)
    if len(cuts) == 1:
        return {
            'type': 'continuant',
            'frames': [parameterize(cuts[0])],
        }
    else:
        frames = []
        for i, cut in enumerate(cuts):
            print('frame', i)
            frames.append(parameterize(cut))
        return {
            'type': 'stop',
            'duration': sum(len(cut) for cut in cuts),
            'frames': frames,
        }

def get_spectrum(formants, n):
    from scipy import signal
    spectrum = [0]*(n // 2 + 1)
    for formant in formants:
        w = formant['freq'] / SAMPLE_RATE * 2*math.pi
        p = cmath.rect(1.0 - formant['width'], w);
        z_w = cmath.rect(1.0, w);
        gain = formant['amp'] * abs((z_w - p) * (z_w - p.conjugate()));
        b, a = signal.zpk2tf([], [p, p.conjugate()], gain)
        w, h = signal.freqz(b, a, n // 2 + 1, include_nyquist=True)
        for i in range(len(spectrum)):
            spectrum[i] += h[i]
    return [float(abs(i)) for i in spectrum]

def plot_spectrum(formants, n, plot):
    plot.plot(get_spectrum(formants, n))

def energy_transfer(formants, n):
    return sum(i ** 2 for i in get_spectrum(formants, n))

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
            dpc.transforms.Grid(4200, 2, grid_w),
            (dpc.transforms.Default('wby'), 3),
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
        n = calc_n(x)
        with open(out_file_path) as file:
            params = json.loads(file.read())
        t = plot.transform(-20, 0, 0, plot.series)
        t.update({'r': 255, 'g': 0, 'b': 255})
        plot.text(phonetic, **t)
        plot.plot([float(abs(i)) / math.sqrt(n) for i in fft(x[:n])[:n//2+1]])
        plot.plot(calc_envelope(x, n))
        plot_spectrum(params['frames'][0]['formants'], n, plot)
    else:
        print(phonetic)
        if phonetic == '0':
            params = analyze()
        else:
            x = load(args.phonetics_file_path, (i * 10 + 4) * SAMPLE_RATE, 4 * SAMPLE_RATE)
            params = analyze(x)
        params = json.dumps(params, indent=2)
        print(params)
        with open(out_file_path, 'w') as file:
            file.write(params)
if args.plot_spectra:
    plot.show()
