import dansplotcore as dpc
from numpy.fft import rfft, irfft
import soundfile as sf

import argparse
import math
import random

parser = argparse.ArgumentParser()
parser.add_argument('--flac')
args = parser.parse_args()

# I think this is a reasonable definition for power in a sound signal.
# We need to differentiate to get a physical quantity that carries energy.
# For example, a DC sound signal carries no energy, but calculating the energy of the signal can be nonzero.
# For a DC air velocity signal, it makes sense for the signal to carry energy.
def power(x):
    dxdt = [
        x[(i+1) % len(x)] - x[i]
        for i in range(len(x))
    ]
    return float(sum(i ** 2 for i in dxdt) / len(x))

def power_ft(x):
    fx = rfft(x)
    afx = [abs(i) for i in fx]
    ifafx = irfft(afx)
    return power(ifafx)

# We want to know the power in an FT of x with phase information discarded.
def cmp_powers(name, f):
    x = [f(i) for i in range(512)]
    print(name, power(x), power_ft(x))

cmp_powers('random', lambda i: random.uniform(-1, 1))
cmp_powers('sin', lambda i: math.sin(i))
cmp_powers('harmonics', lambda i: math.sin(i) + math.sin(2 * i))

if args.flac:
    data, sample_rate = sf.read(args.flac)
    powers = []
    powers_ft = []
    for i in range(0, len(data), 64):
        x = data[i:i+512]
        powers.append(power(x))
        powers_ft.append(power_ft(x))
        percent = i / len(data) * 100
        print(f'{percent:5.1f}%', end='\r')
    print()
    dpc.plot([powers, powers_ft])
