import dansplotcore as dpc
from scipy import signal

import cmath
import math

tau = 2 * math.pi
s = 44100
t_o = 20
t_c = 8000
n_c = 8000

h_total = [0] * (1 << 16)

def add(b, a):
    w, h = signal.freqz(b, a, len(h_total))
    for i in range(len(h_total)):
        h_total[i] += h[i]

for i in range(t_o):
    w_full = tau * (i + 1) / t_o
    w = w_full * t_c / s
    width = 0.01
    p = cmath.rect(1 - width, w)
    z_w = cmath.rect(1, w)
    b0 = abs((z_w - p) * (z_w - p.conjugate()))
    a1 = -(p + p.conjugate()).real
    a2 = (p * p.conjugate()).real
    add([b0], [1, a1, a2])

w = tau * n_c / s
alpha = 1 / (w + 1)
a1 = -alpha
b0 = alpha
b1 = -alpha
add([b0, b1], [1, a1])

dpc.plot(
    [i / len(h_total) * s / 2 for i in range(len(h_total))],
    [float(abs(i)) for i in h_total],
)
