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
                if flip == None:
                    flip = int(os.environ.get('DLAL_PAN_FLIP', '0'))
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

    def set(
        self,
        angle,
        distance=None,
        *,
        flip=False,
        ear_offset=0.1,
        speed_of_sound=343,
        sample_rate=None,
    ):
        if flip: angle += 180
        angle *= math.tau / 360
        power = (math.sin(angle) + 1) / 2
        gain = math.sqrt(power)
        self.gain(gain)
        if distance != None:
            x_src = distance * math.sin(angle)
            y_src = distance * math.cos(angle)
            x_ear = ear_offset  # no flipping - angle already flipped if requested
            y_ear = 0
            d = math.sqrt((x_src - x_ear) ** 2 + (y_src - y_ear) ** 2)
            delay = d / speed_of_sound
            self.delay(delay, sample_rate=sample_rate)
