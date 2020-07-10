from ._component import Component

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
