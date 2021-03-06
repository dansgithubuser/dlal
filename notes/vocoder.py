import dansplotcore as dpc
from scipy import signal

import math

s = 44100
t_i = 0
t_o = 20
t_c = 8000
n_c = 8000

# globals
h_total = [0] * (1 << 16)

# helpers
def add(b, a):
    w, h = signal.freqz(b, a, len(h_total))
    for i in range(len(h_total)):
        h_total[i] += h[i]

def add_narrow(f, q_value):
    omega = 2 * math.pi * f / s
    omega_s = math.sin(omega)
    omega_c = math.cos(omega)
    alpha = omega_s / (2.0 * q_value);
    b0 = omega_s / 2.0;
    b1 = 0.;
    b2 = -(omega_s / 2.0);
    a0 = 1.0 + alpha;
    a1 = -2.0 * omega_c;
    a2 = 1.0 - alpha;
    add([b0 / a0, b1 / a0, b2 / a0], [1, a1 / a0, a2 / a0])

def add_high_pass(f, q_value):
    omega = 2 * math.pi * f / s
    omega_s = math.sin(omega)
    omega_c = math.cos(omega)
    alpha = omega_s / (2.0 * q_value);
    b0 = (1.0 + omega_c) * 0.5;
    b1 = -(1.0 + omega_c);
    b2 = (1.0 + omega_c) * 0.5;
    a0 = 1.0 + alpha;
    a1 = -2.0 * omega_c;
    a2 = 1.0 - alpha;
    add([b0 / a0, b1 / a0, b2 / a0], [1, a1 / a0, a2 / a0])

# populate frequency response
for i in range(t_i, t_o):
    add_narrow((i + 1) / t_o * t_c, 25 + i / 2)

add_high_pass(n_c, 1 / math.sqrt(2))

# plot
dpc.plot(
    [i / len(h_total) * s / 2 for i in range(1, len(h_total))],
    [20 * math.log10(float(abs(i))) for i in h_total[1:]],
)
