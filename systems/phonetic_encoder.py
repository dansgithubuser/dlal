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
    'and transforms each into an FIR, a tone amplitude, and a noise amplitude.'
)
parser.add_argument('dir')
parser.add_argument('--frequency', '-f', help='frequency of voiced phonetic', default=80)
parser.add_argument('--frequency-deviation', '--fd', default=20)
args = parser.parse_args()

#===== consts =====#
SAMPLE_RATE = 44100

#===== helpers =====#
def autocorrelation(x, shift):
    error = 0
    total = 0
    for i in range(len(x)-shift):
        error += abs(x[i] - x[i+shift])
        total += abs(x[i])
    print(error, total, 1 - error / total / 2)
    return 1 - error / total / 2

def sigmoid(x, x0=0, k=1):
    return 1 / (1 + math.exp(-k*(x-x0)))

def exp(x, base):
    return (base**x - 1) / (base - 1)

def analyze(wav_file_path):
    # load
    buf = dlal.Buf()
    buf.load(wav_file_path, 0)
    x = [float(i) for i in buf.to_json()['0']['samples']]
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

#===== main =====#
for wav_file_path in glob.glob(args.dir+'/*.wav'):
    print(wav_file_path)
    params = analyze(wav_file_path)
    out_file_path = re.sub('.wav$', '', wav_file_path) + '.phonetic.json'
    with open(out_file_path, 'w') as file:
        file.write(json.dumps(params))
