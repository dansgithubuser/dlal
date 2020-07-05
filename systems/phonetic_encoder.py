#===== imports =====#
import dlal

import argparse
import json
import math
import os
import re

#===== args =====#
parser = argparse.ArgumentParser(description=
    'Takes a sound as recorded by phonetic_recorder.py, '
    'and transforms into phonetic parameters that can be consumed by phonetic_decoder.py.'
)
parser.add_argument('--phonetics-file-path', default='assets/phonetics/phonetics.flac')
parser.add_argument('--only')
parser.add_argument('--start-from')
parser.add_argument('--frequency', '-f', help='frequency of voiced phonetic', default=100)
parser.add_argument('--frequency-deviation', '--fd', default=7)
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
    error = 0
    total = 0
    for i in range(len(x)-shift):
        error += abs(x[i] - x[i+shift])
        total += abs(x[i])
    print(error, total, 1 - error / total / 2)
    return 1 - error / total / 2

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

def exp(x, base):
    return (base**x - 1) / (base - 1)

def parameterize(x):
    # autocorrelation
    f_i = float(args.frequency) - float(args.frequency_deviation)
    f_f = float(args.frequency) + float(args.frequency_deviation)
    shift_i = int(SAMPLE_RATE / f_f)
    shift_f = int(SAMPLE_RATE / f_i)
    max_ac = -1
    for shift in range(shift_i, shift_f):
        while shift >= len(x):
            shift //= 2
        ac = autocorrelation(x, shift)
        if ac > max_ac: max_ac = ac
    # average amplitude
    avg_amp = sum(abs(i) for i in x) / len(x)
    # outputs
    return {
        'fir': x[:64],
        'tone_amp': avg_amp * exp(max_ac, 10),
        'noise_amp': avg_amp * exp(1-max_ac, 10),
    }

def analyze(x):
    ranges = stop_ranges(x)
    if ranges:
        i_i, i_f = ranges[0]
        duration = i_f - i_i
        i_step = duration // 3
        frames = []
        for i in range(i_i, i_f, i_step):
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
    'ae', 'ay', 'aw', 'e', 'ee', 'i', 'o', 'oo', 'uu', 'uh',
    'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z', 'm', 'n', 'ng', 'r', 'l',
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]
for i, phonetic in enumerate(phonetics):
    if args.only and phonetic != args.only:
        continue
    if args.start_from and i < phonetics.index(args.start_from):
        continue
    print(phonetic)
    x = load(args.phonetics_file_path, (i * 10 + 4) * SAMPLE_RATE, 4 * SAMPLE_RATE)
    params = analyze(x)
    out_file_path = os.path.join(
        os.path.dirname(args.phonetics_file_path),
        phonetic + '.phonetic.json',
    )
    params = json.dumps(params, indent=2)
    print(params)
    with open(out_file_path, 'w') as file:
        file.write(params)
