from .skeleton import *

import json
import os

class Audio(Component):
    def __init__(self, **kwargs):
        Component.__init__(self, 'audio', **kwargs)
        self.device_info = None

    def _find_device(self, env_var):
        namish = os.environ.get(env_var)
        if namish is not None:
            if self.device_info is None:
                self.device_info = json.loads(self.command('probe', immediate=True))
            for i, v in enumerate(self.device_info):
                if namish in v['name']:
                    return i
        return -1

    def start(self, immediate=True):
        self.command('start',
            self._find_device('DLAL_AUDIO_INPUT'),
            self._find_device('DLAL_AUDIO_OUTPUT'),
            immediate=immediate,
        )

    def finish(self, immediate=True):
        self.command('finish', immediate=immediate)
