from ._component import Component

class Addsyn(Component):
    def __init__(self, preset=None, **kwargs):
        Component.__init__(self, 'addsyn', **kwargs)

    def rissets_bell(self, duration=4, sample_rate=44100):
        t = 1 / duration / sample_rate
        self.partials([
            {'v': 0.10, 'a': 1, 'd':  1.0*t, 's': 0, 'r': 1, 'm': 0.56, 'b': 0.0},
            {'v': 0.07, 'a': 1, 'd':  1.1*t, 's': 0, 'r': 1, 'm': 0.56, 'b': 1.0},
            {'v': 0.10, 'a': 1, 'd':  1.5*t, 's': 0, 'r': 1, 'm': 0.92, 'b': 0.0},
            {'v': 0.18, 'a': 1, 'd':  1.8*t, 's': 0, 'r': 1, 'm': 0.92, 'b': 1.7},
            {'v': 0.27, 'a': 1, 'd':  3.1*t, 's': 0, 'r': 1, 'm': 1.19, 'b': 0.0},
            {'v': 0.17, 'a': 1, 'd':  2.8*t, 's': 0, 'r': 1, 'm': 1.70, 'b': 0.0},
            {'v': 0.15, 'a': 1, 'd':  4.0*t, 's': 0, 'r': 1, 'm': 2.00, 'b': 0.0},
            {'v': 0.13, 'a': 1, 'd':  5.0*t, 's': 0, 'r': 1, 'm': 2.74, 'b': 0.0},
            {'v': 0.13, 'a': 1, 'd':  6.6*t, 's': 0, 'r': 1, 'm': 3.00, 'b': 0.0},
            {'v': 0.10, 'a': 1, 'd':  9.8*t, 's': 0, 'r': 1, 'm': 3.76, 'b': 0.0},
            {'v': 0.13, 'a': 1, 'd': 14.3*t, 's': 0, 'r': 1, 'm': 4.07, 'b': 0.0},
        ])
        return self
