import obvious

import collections
import ctypes
import functools
import json
import os
import weakref

DIR = os.path.dirname(os.path.realpath(__file__))
COMPONENTS_DIR = os.path.join(DIR, '..', '..', 'components')

def component_kinds(special=None):
    avoid = []
    if special is not None:
        special_kinds = [
            i[:-3]
            for i in os.listdir(DIR)
            if not i.startswith('_')
        ]
        if special is True: return special_kinds
        avoid = special_kinds
    return [
        i
        for i in os.listdir(COMPONENTS_DIR)
        if not i.startswith('base') and i not in avoid
    ]

def _json_prep(args, kwargs):
    def prep(x):
        if type(x) == bool:
            return '1' if x else '0'
        elif type(x) in [int, float]:
            return str(x)
        else:
            return x
    return [prep(i) for i in args], {k: prep(v) for k, v in kwargs.items()}

class Component:
    def __init__(self, kind, name=None):
        # tracking
        if name == None:
            name = kind
            num = 1
            while name in Component._components:
                num += 1
                name = kind + str(num)
        elif name in Component._components:
            raise Exception('name must be unique')
        self.name = name
        self.kind = kind
        Component._components[name] = weakref.proxy(self)
        # raw
        self._lib = Component._load_lib(kind)
        self._raw = self._lib.construct()
        # typical commands
        for item in self.command_immediate('list'):
            if hasattr(self, item['name']): continue
            setattr(
                self,
                item['name'],
                functools.partial(self.command, item['name']),
            )

    def __del__(self):
        del Component._components[self.name]
        self._lib.destruct(self._raw)

    def command(self, name, *args, **kwargs):
        args, kwargs = _json_prep(args, kwargs)
        if Component._comm:
            return Component._comm.queue(self, name, *args, **kwargs)
        else:
            return self.command_immediate(name, *args, **kwargs)

    def command_immediate(self, name, *args, **kwargs):
        args, kwargs = _json_prep(args, kwargs)
        result = self._lib.command(self._raw, json.dumps({
            'name': name,
            'args': args,
            'kwargs': kwargs,
        }).encode('utf-8'))
        if not result: return
        result = json.loads(result.decode('utf-8'))
        if type(result) == dict and 'error' in result:
            raise Exception(result['error'])
        return result

    def connect(self, other, toggle=False):
        if toggle and other.name in Component._connections.get(self.name, []):
            result = self.command('disconnect', *other._view())
            Component._connections[self.name].remove(other.name)
        else:
            result = self.command('connect', *other._view())
            Component._connections[self.name].append(other.name)
        return result

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

    def _view(self):
        return [
            str(self._raw),
            str(ctypes.cast(self._lib.command , ctypes.c_void_p).value),
            str(ctypes.cast(self._lib.midi    , ctypes.c_void_p).value),
            str(ctypes.cast(self._lib.audio   , ctypes.c_void_p).value),
            str(ctypes.cast(self._lib.evaluate, ctypes.c_void_p).value),
        ]

    _libs = {}
    _components = {}
    _connections = collections.defaultdict(list)
    _comm = None

def queue_set(comm):
    Component._comm = comm
