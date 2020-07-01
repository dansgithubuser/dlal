#===== imports =====#
import dlal

import argparse
import glob
import json
import math
import re

#===== args =====#
parser = argparse.ArgumentParser(description=
    'Takes a folder full of wav files that consist of 5 seconds of a single phonetic, '
    'and transforms each into phonetic parameters that can be consumed by phonetic_decoder.py.'
)
parser.add_argument('dir')
parser.add_argument('--only')
parser.add_argument('--frequency', '-f', help='frequency of voiced phonetic', default=80)
parser.add_argument('--frequency-deviation', '--fd', default=20)
args = parser.parse_args()

#===== consts =====#
SAMPLE_RATE = 44100

#===== helpers =====#
def load(wav_file_path):
    buf = dlal.Buf()
    buf.load(wav_file_path, 0)
    return [float(i) for i in buf.to_json()['0']['samples']]

def autocorrelation(x, shift):
    error = 0
    total = 0
    for i in range(len(x)-shift):
        error += abs(x[i] - x[i+shift])
        total += abs(x[i])
    print(error, total, 1 - error / total / 2)
    return 1 - error / total / 2

def plosive_ranges(x):
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
    # if threshold is close to maximum, this isn't a plosive
    maximum = sorted_envelope[-1]
    if threshold / maximum > 1 / silence_factor:
        return None
    # figure plosive starts
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
    ranges = plosive_ranges(x)
    if ranges:
        i_i, i_f = ranges[0]
        i_step = (i_f - i_i) // 3
        frames = []
        for i in range(i_i, i_f, i_step):
            print(i, i+i_step)
            frames.append(parameterize(x[i:i+i_step]))
        return {
            'type': 'plosive',
            'frames': frames,
        }
    else:
        return parameterize(x)

#===== main =====#
for wav_file_path in glob.glob(args.dir+'/*.wav'):
    if args.only and not wav_file_path[:-4].endswith(args.only):
        continue
    print(wav_file_path)
    x = load(wav_file_path)
    params = analyze(x)
    out_file_path = re.sub('.wav$', '', wav_file_path) + '.phonetic.json'
    with open(out_file_path, 'w') as file:
        file.write(json.dumps(params))
