from ._component import Component

import cmath
import math

class Iir(Component):
    def __init__(self, b=None, a=None, **kwargs):
        Component.__init__(self, 'iir', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if a: self.a(a)
            if b: self.b(b)

    def a(self, a=None):
        args = []
        if a != None: args.append(a)
        return self.command('a', args, do_json_prep=False)

    def b(self, b=None):
        args = []
        if b != None: args.append(b)
        return self.command('b', args, do_json_prep=False)

    def single_pole_bandpass(self, w, width, peak=1, smooth=0):
        assert 0 < width < 1
        # How would we get a peak of 1?
        # H(z) = gain / ((z - p)*(z - p.conjugate()))
        # We can control gain
        # Max response is at z_w = cmath.rect(1, w)
        # gain = abs((z_w - p)*(z_w - p.conjugate()))
        p = cmath.rect(1 - width, w)
        z_w = cmath.rect(1, w)
        gain = peak * abs((z_w - p)*(z_w - p.conjugate()))
        self.command(
            'pole_zero',
            [
                [
                    { 're': p.real, 'im': +p.imag },
                    { 're': p.real, 'im': -p.imag },
                ],
                [],
                str(gain),
            ],
            {'smooth': smooth},
            do_json_prep=False,
        )
