from .skeleton import *

class Audio(Component):
    def __init__(self, **kwargs):
        Component.__init__(self, 'audio', **kwargs)

    def start(self):
        self.command('start', immediate=True)

    def finish(self):
        self.command('finish', immediate=True)
