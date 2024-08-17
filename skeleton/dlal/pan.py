from ._component import Component

import math
import os

class Pan(Component):
    def __init__(
        self,
        angle=None,
        distance=None,
        *,
        flip=None,
        ear_offset=0.1,
        speed_of_sound=343,
        sample_rate=None,
        **kwargs,
    ):
        Component.__init__(self, 'pan', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if angle != None:
                self.set(
                    angle,
                    distance,
                    flip=flip,
                    ear_offset=ear_offset,
                    speed_of_sound=speed_of_sound,
                    sample_rate=sample_rate
                )

    def __str__(self):
        return f'{self.name}({self.gain():.2f}, {self.delay():.3f})'
