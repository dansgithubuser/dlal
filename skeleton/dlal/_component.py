from . import _logging
from ._utils import DIR

import obvious

import collections
import ctypes
import inspect
import json
import os
import types
import weakref

log = _logging.get_log(__name__)

COMPONENTS_DIR = os.path.join(DIR, '..', '..', 'components')

def component_kinds(special=None):
    avoid = [
        'Cargo.lock',
        'Cargo.toml',
    ]
    if special is not None:
        special_kinds = [
            i[:-3]
            for i in os.listdir(DIR)
            if not i.startswith('_') and i.endswith('.py')
        ]
        if special is True: return special_kinds
        avoid.extend(special_kinds)
    return [
        i
        for i in os.listdir(COMPONENTS_DIR)
        if not i.startswith('base') and i not in avoid
    ]

class Component:
    _libs = {}
    _components = {}
    _connections = collections.defaultdict(dict)
    _driver = None
    _comm = None
    _detach = False

    def __init__(self, kind, name=None, slot=0, preadd=None):
        # tracking
        if name == None:
            name = kind
            num = 1
            while name in Component._components:
                num += 1
                name = kind + str(num)
        elif name in Component._components:
            raise Exception('name must be unique')
        log('debug', f'init {name}')
        self.name = name
        self.kind = kind
        Component._components[name] = weakref.proxy(self)
        # raw
        self._lib = Component._load_lib(kind)
        self._raw = self._lib.construct(name.encode('utf-8'))
        # typical commands
        def make_typical_command(name):
            def typical_command(self, *args, **kwargs):
                return self.command(name, args, kwargs)
            return types.MethodType(typical_command, self)
        for item in self.command_immediate('list'):
            if hasattr(self, item['name']): continue
            setattr(
                self,
                item['name'],
                make_typical_command(item['name']),
            )
        if Component._driver:
            if preadd: preadd()
            Component._driver.add(self, slot)

    def __del__(self):
        if hasattr(self, 'deleted'):
            return
        del Component._components[self.name]
        self._lib.destruct(self._raw)
        self.deleted = True

    def __repr__(self):
        return self.name

    def command(self, name, args=[], kwargs={}, timeout_ms=20):
        if Component._comm:
            log('debug', f'{self.name} queue {name} {args} {kwargs}')
            return Component._comm.queue(self, name, args, kwargs, timeout_ms=timeout_ms, detach=self._detach)
        else:
            return self.command_immediate(name, args, kwargs)

    def command_detach(self, name, args=[], kwargs={}):
        if Component._comm:
            log('debug', f'{self.name} queue (detach) {name} {args} {kwargs}')
            return Component._comm.queue(self, name, args, kwargs, detach=True)
        else:
            return self.command_immediate(name, args, kwargs)

    def command_immediate(self, name, args=[], kwargs={}):
        log('debug', f'{self.name} {name} {args} {kwargs}')
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

    def list(self):
        def py(command):
            spec = inspect.getfullargspec(command)
            doc = inspect.getdoc(command)
            result = {'args': spec.args}
            if spec.varargs: result['varargs'] = spec.varargs
            if spec.varkw: result['varkw'] = spec.varkw
            if spec.defaults: result['defaults'] = spec.defaults
            if doc: result['doc'] = doc
            return result
        result = self.command_immediate('list')
        covered = []
        for i in result:
            if i['name'] == 'name':
                continue
            command = getattr(self, i['name'])
            i['py'] = py(command)
            covered.append(i['name'])
        py_only = []
        for k, v in inspect.getmembers(self):
            if k.startswith('_') and k != '__init__': continue
            if not callable(v): continue
            if k in covered: continue
            if v.__func__ == getattr(Component, k, None): continue
            py_only.append({
                'name': k,
                'py': py(v),
            })
        return py_only + result

    def connect(self, other, *, toggle=False, **extra):
        if os.environ.get('DLAL_SNOOP_CONNECT'):
            print(f'connect {self.name} {other.name}')
        else:
            log('debug', f'connect {self.name} {other.name}')
        if toggle and other.name in Component._connections.get(self.name, {}):
            result = self.command('disconnect', other._view())
            del Component._connections[self.name][other.name]
        else:
            result = self.command('connect', other._view(), extra)
            Component._connections[self.name][other.name] = extra
        return result

    def disconnect(self, other):
        log('debug', f'disconnect {self.name} {other.name}')
        result = self.command('disconnect', other._view())
        connections = Component._connections[self.name]
        if other.name in connections: del connections[other.name]
        return result

    def midi(self, msg):
        if isinstance(msg, list) and isinstance(msg[0], list):
            return [self.command('midi', [i]) for i in msg]
        return self.command('midi', [msg])

    def _load_lib(kind):
        if kind in Component._libs: return Component._libs[kind]
        lib = obvious.load_lib(
            kind,
            paths=[
                os.path.join(COMPONENTS_DIR, 'target', 'release'),  # dev
            ],
        )
        obvious.set_ffi_types(lib.construct, 'void*', str)
        obvious.set_ffi_types(lib.destruct, None, 'void*')
        obvious.set_ffi_types(lib.command, str, 'void*', str)
        Component._libs[kind] = lib
        return lib

    def _view(self):
        return [
            str(self._raw),
            str(ctypes.cast(self._lib.command, ctypes.c_void_p).value),
            str(ctypes.cast(self._lib.midi   , ctypes.c_void_p).value),
            str(ctypes.cast(self._lib.audio  , ctypes.c_void_p).value),
            str(ctypes.cast(self._lib.run    , ctypes.c_void_p).value),
        ]

def comm_set(comm):
    Component._comm = comm
