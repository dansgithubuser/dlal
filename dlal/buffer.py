from .skeleton import *
from .helpers import *
from .sonic_controller import *

import math
import os

class Buffer(Component):
    def __init__(self, **kwargs):
        Component.__init__(self, 'buffer', **kwargs)
        self.known_sounds = {}
        for path, folders, files in os.walk(os.path.join('..', '..', 'components', 'buffer', 'sounds')):
            for file in files:
                name, extension = os.path.splitext(file)
                if extension != '.wav':
                    continue
                self.known_sounds[name] = os.path.join(path, file)

    def render_simple_system(self, note_number, simple_system):
        assert simple_system.test
        simple_system.standard_system_functionality()
        self.load_raw(note_number, 'raw.txt', immediate=True)

    def render_sonic_drums(self):
        self.render_simple_system(0x3c, SimpleSystem([SonicController('snare')], test=True, test_duration=250))
        commander = Component('commander')
        sonic_controller = SonicController('badassophone')
        for i in range(250):
            commander.queue(i, sonic_controller, 'frequency_multiplier', 0.97 ** i, immediate=True)
        self.render_simple_system(0x3e, SimpleSystem([sonic_controller, commander], test=True, test_duration=250))
        self.render_simple_system(0x40, SimpleSystem([SonicController('ride')], test=True, test_duration=250))

    def load_sound(self, note_number, file_name):
        if file_name in self.known_sounds:
            file_name = self.known_sounds[file_name]
        return self.command('load_sound {} {}'.format(note_number, file_name), immediate=True)

    def load_sounds(self):
        known_sounds = self.known_sounds.items()
        known_sounds = sorted(known_sounds, key=lambda x: x[1])
        i = 0
        for file_name, path in known_sounds:
            self.load_sound(i, path)
            i += 1
            if i == 128:
                break

    def lfo(self, period_in_samples):
        period = [str(math.sin(2*math.pi*x/period_in_samples)) for x in range(period_in_samples)]
        self.read_sound(0, ' '.join(period), immediate=True)
        self.repeat_sound('y', immediate=True)
