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
