from ._component import Component

import math

class Iir(Component):
    def __init__(self, b=[1], a=[], **kwargs):
        Component.__init__(self, 'iir', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            self.a(a)
            self.b(b)

    def a(self, a):
        return self.command('a', [a], do_json_prep=False)

    def b(self, b):
        return self.command('b', [b], do_json_prep=False)

    def frequency_response(b=[1], a=[], steps=1024, sample_rate=44100):
        a = [1] + a
        result = []
        for i in range(steps):
            f = 10 ** (math.log10(sample_rate/2) * i / (steps-1))
            w = 2 * math.pi * f / sample_rate
            z = math.e ** (1j*w)
            h = (
                sum(b_i * z ** -i for i, b_i in enumerate(b))
                /
                sum(a_i * z ** -i for i, a_i in enumerate(a))
            )
            result.append((
                f,
                20 * math.log10(abs(h)),
            ))
        return result
