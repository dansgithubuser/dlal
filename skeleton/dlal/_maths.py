import math as _math
import random as _random

#===== generator =====#
def define_phase(sample_rate):
    class Phase:
        def __init__(self):
            self.value = 0
        def __iadd__(self, freq):
            self.value += freq / sample_rate
            self.value %= 1
            return self
    return Phase

class Generator:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.Phase = define_phase(sample_rate)
        self.duration = 1
        self.init()

    def generate(self):
        samples = []
        while True:
            t = len(samples) / self.sample_rate
            if t > self.duration: break
            samples.append(self.amp(t))
        return samples

    def sqr(self, phase):
        if phase.value < 0.5:
            return -1
        else:
            return +1

    def saw(self, phase):
        return 2 * phase.value - 1

    def sin(self, phase):
        return _math.sin(_math.tau * phase.value)

    def rand(self):
        return _random.random() * 2 - 1

    def ramp(self, a, b, t):
        if t < 0: return a
        if t > 1: return b
        return (1 - t) * a + t * b

    def clamp(self, x, a=-1, b=1):
        if x < a: return a
        if x > b: return b
        return x

#===== helpers =====#
class Lpf:
    def __init__(self):
        self.y = 0

    def __call__(self, x, lowness):
        self.y = (1-lowness) * x + lowness * self.y
        return self.y

class Hpf:
    def __init__(self):
        self.x = 0
        self.y = 0

    def __call__(self, x, highness):
        self.y = (1-highness) * (self.y + x - self.x)
        self.x = x
        return self.y

#===== instruments =====#
#----- drums -----#
def drum(
    *,
    sample_rate=44100,
    duration,
    bodies=[],
    tail_amp=0,
    lo_i=0,
    lo_f=0,
    hi_i=0,
    hi_f=0,
):
    class Drum(Generator):
        def init(self):
            self.duration = duration
            self.bodies = [[*body, self.Phase()] for body in bodies]
            self.lpf1 = Lpf()
            self.lpf2 = Lpf()
            self.hpf1 = Hpf()
            self.hpf2 = Hpf()

        def amp(self, t):
            envelope = 0.01 ** self.ramp(0, 1, t / self.duration)
            x = tail_amp * self.rand() * envelope
            for freq_i, freq_f, amp, duration, phase in self.bodies:
                if t > duration: continue
                phase += self.ramp(freq_i, freq_f, t / duration)
                envelope = 0.01 ** self.ramp(0, 1, t / duration)
                x += amp * self.sin(phase) * envelope
            lowness = self.ramp(lo_i, lo_f, t / self.duration)
            x = self.lpf1(x, lowness)
            x = self.lpf2(x, lowness)
            highness = self.ramp(hi_i, hi_f, t / self.duration)
            x = self.hpf1(x, highness)
            x = self.hpf2(x, highness)
            return self.clamp(x)

    return Drum(sample_rate).generate()

def kick(
    *,
    sample_rate=44100,
    duration=0.2,
    body_freq_i=120,
    body_freq_f=0,
    body_amp=1,
    tail_amp=0,
):
    return drum(
        sample_rate=sample_rate,
        duration=duration,
        bodies=[(body_freq_i, body_freq_f, body_amp, duration)],
        tail_amp=tail_amp,
    )

def snare(
    *,
    sample_rate=44100,
    duration=0.25,
    body_freq1_i=200,
    body_freq1_f=150,
    body_amp1=1,
    body_freq2_i=400,
    body_freq2_f=370,
    body_amp2=1,
    tail_amp=1,
    lo_i=0.1,
    lo_f=0.8,
    hi_i=0,
    hi_f=0.4,
):
    return drum(
        sample_rate=sample_rate,
        duration=duration,
        bodies=[
            (body_freq1_i, body_freq1_f, body_amp1, duration),
            (body_freq2_i, body_freq2_f, body_amp2, duration/3),
        ],
        tail_amp=tail_amp,
        lo_i=lo_i,
        lo_f=lo_f,
        hi_i=hi_i,
        hi_f=hi_f,
    )

def floor_tom(
    *,
    sample_rate=44100,
    duration=0.3,
    body_freq_i=100,
    body_freq_f=40,
    body_amp=0.75,
    tail_amp=0.25,
):
    return drum(
        sample_rate=sample_rate,
        duration=duration,
        bodies=[(body_freq_i, body_freq_f, body_amp, duration)],
        tail_amp=tail_amp,
    )

def low_tom(
    *,
    sample_rate=44100,
    duration=0.25,
    body_freq_i=160,
    body_freq_f=60,
    body_amp=0.75,
    tail_amp=0.25,
):
    return drum(
        sample_rate=sample_rate,
        duration=duration,
        bodies=[(body_freq_i, body_freq_f, body_amp, duration)],
        tail_amp=tail_amp,
    )

def mid_tom(
    *,
    sample_rate=44100,
    duration=0.2,
    body_freq_i=200,
    body_freq_f=140,
    body_amp=0.75,
    tail_amp=0.25,
):
    return drum(
        sample_rate=sample_rate,
        duration=duration,
        bodies=[(body_freq_i, body_freq_f, body_amp, duration)],
        tail_amp=tail_amp,
    )

def high_tom(
    *,
    sample_rate=44100,
    duration=0.15,
    body_freq_i=260,
    body_freq_f=220,
    body_amp=0.5,
    tail_amp=0.5,
):
    return drum(
        sample_rate=sample_rate,
        duration=duration,
        bodies=[(body_freq_i, body_freq_f, body_amp, duration)],
        tail_amp=tail_amp,
    )
