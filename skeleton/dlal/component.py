import obvious

import ctypes
import json
import os

DIR = os.path.dirname(os.path.realpath(__file__))
COMPONENTS_DIR = os.path.join(DIR, '..', '..', 'components')

class Component:
    _libs = {}

    def _load_lib(kind):
        if kind in Component._libs: return Component._libs[kind]
        lib = obvious.load_lib(
            kind,
            paths=[
                os.path.join(COMPONENTS_DIR, kind, 'target', 'release'),  # dev
            ],
        )
        obvious.set_ffi_types(lib.construct, 'void*')
        obvious.set_ffi_types(lib.destruct, None, 'void*')
        obvious.set_ffi_types(lib.command, str, 'void*', str)
        Component._libs[kind] = lib
        return lib

    def __init__(self, kind, name=None):
        if name == None: name = kind
        self._lib = Component._load_lib(kind)
        self._raw = self._lib.construct()

    def __del__(self):
        self._lib.destruct(self._raw)

    def command(self, name, *args, **kwargs):
        result = self._lib.command(self._raw, json.dumps({
            'name': name,
            'args': args,
            'kwargs': kwargs,
        }).encode('utf-8'))
        if not result: return
        result = json.loads(result.decode('utf-8'))
        if 'error' in result:
            raise Exception(result['error'])
        return result

    def connect(self, other):
        return self.command('connect', *other._view())

    def _view(self):
        return [
            str(self._raw),
            str(ctypes.cast(self._lib.command , ctypes.c_void_p).value),
            str(ctypes.cast(self._lib.midi    , ctypes.c_void_p).value),
            str(ctypes.cast(self._lib.audio   , ctypes.c_void_p).value),
            str(ctypes.cast(self._lib.evaluate, ctypes.c_void_p).value),
        ]
