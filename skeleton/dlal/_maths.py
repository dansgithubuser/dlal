import math as _math

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
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self.Phase = define_phase(sample_rate)
        self.init()

    def generate(self):
        samples = []
        while True:
            a = self.amp(len(samples) / self.sample_rate)
            if a == None: break
            samples.append(a)
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

    def ramp(self, a, b, t):
        if t < 0: return a
        if t > 1: return b
        return (1 - t) * a + t * b
