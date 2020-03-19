import obvious

import glob
import json
import os

DIR = os.path.dirname(os.path.realpath(__file__))

class Component:
    _libs = {}

    def _load_lib(kind):
        if kind in Component._libs: return Component._libs[kind]
        lib = obvious.load_lib(
            kind,
            paths=[os.path.join(DIR, '..', 'components', kind, 'target', 'release')],
        )
        obvious.set_ffi_types(lib.construct, 'void*')
        obvious.set_ffi_types(lib.destruct, None, 'void*')
        obvious.set_ffi_types(lib.command, str, 'void*', str)
        Component._libs[kind] = lib
        return lib

    def __init__(self, kind, name=None):
        if name == None: name = kind
        self.lib = Component._load_lib(kind)
        self.raw = self.lib.construct()

    def __del__(self):
        self.lib.destruct(self.raw)

    def command(self, name, *args, **kwargs):
        result = self.lib.command(self.raw, json.dumps({
            'name': name,
            'args': args,
            'kwargs': kwargs,
        }).encode('utf-8'))
        if result: return json.loads(result.decode('utf-8'))
