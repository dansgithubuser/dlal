from ._component import Component

import math

class Iir(Component):
    def __init__(self, b=None, a=None, **kwargs):
        Component.__init__(self, 'iir', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if a: self.a(a)
            if b: self.b(b)

    def a(self, a):
        return self.command('a', [a], do_json_prep=False)

    def b(self, b):
        return self.command('b', [b], do_json_prep=False)

    def pole_zero(self, p, z, k=1):
        from scipy import signal
        if len(p) and type(p[0]) == dict:
            p = [i['re'] + 1j * i['im'] for i in p]
        if len(z) and type(z[0]) == dict:
            z = [i['re'] + 1j * i['im'] for i in z]
        b, a = signal.zpk2tf(z, p, k)
        self.command_detach('a', [list(a)], do_json_prep=False)
        self.command_detach('b', [list(b)], do_json_prep=False)
