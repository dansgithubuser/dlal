import obvious

import glob
import os

DIR = os.path.dirname(os.path.realpath(__file__))

class Component:
    _libs = {}

    def _path(kind):
        return os.path.join(DIR, '..', 'components', kind, 'target', 'release')

    def __init__(self, kind, name=None):
        if name == None: name = kind
        if kind not in Component._libs:
            Component._libs[kind] = obvious.load_lib(kind, paths=[Component._path(kind)])
        Component._libs[kind].start()  # TODO
