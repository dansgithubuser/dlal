from .skeleton import *
from . import helpers

import time

class Filea(Component):
    def __init__(self, **kwargs):
        Component.__init__(self, 'filea', **kwargs)

    def switch_ambience(self, file_name=None, duration=4):
        x = helpers.peruse(os.path.join('..', '..', 'components', 'filea', 'ambient'), file_name, '.ogg')
        if type(x) == list: return x
        self.fade(0, duration/2-0.1)
        time.sleep(duration/2)
        self.open_read(x)
        self.fade(1, duration/2)