from ._component import Component

from ._utils import ASSETS_DIR

import math
import os

class Soundfont(Component):
    def __init__(self, **kwargs):
        Component.__init__(self, 'soundfont', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            self.soundfont_load(ASSETS_DIR / 'soundfont/32MbGMStereo.sf2')
