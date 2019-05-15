from .skeleton import *
from .qweboard import qwe_to_note

class MarkovLiner(Component):
    def __init__(self, period_in_samples=0, samples_per_quarter=22050, **kwargs):
        Component.__init__(self, 'markov_liner', **kwargs)
        if period_in_samples:
            self.periodic_resize(period_in_samples)
        self.samples_per_quarter = samples_per_quarter

    def state_create(self, on, off, duration, immediate=False):
        return self.command('state_create', *(on + [';'] + off + [';', duration]), immediate=immediate)

    def note(self, note, duration, immediate=False):
        return self.state_create([0x90, note, 0x40], [0x80, note, 0x40], duration, immediate=immediate)

    def trans(self, initial, final, weight=1, immediate=False):
        return self.transition_create(initial, final, weight, immediate=immediate)
