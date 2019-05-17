import atexit
import collections
import ctypes
import functools
import inspect
import json
import os
import platform
import re
import subprocess
import sys
import time
import weakref

root = os.path.join(os.path.split(os.path.realpath(__file__))[0], '..')
sys.path.append(os.path.join(root, 'deps', 'dansmidilibs'))
sys.path.append(os.path.join(root, 'deps', 'obvious'))

import midi
import obvious

def invoke(invocation):
    subprocess.check_call(invocation, shell=True)

def snake_case(camel_case):
    return re.sub('(.)([A-Z])', r'\1_\2', camel_case).lower()

def camel_case(snake_case):
    return ''.join([i.capitalize() for i in snake_case.split('_')])

def report(result):
    if result.startswith('error'):
        raise RuntimeError(result)
    elif result.startswith('warning'):
        print(result)
    return result

def connect(*args, immediate=False):
    if len(args) <= 1:
        return
    result = ''
    for i in range(len(args)-1):
        result += args[i].connect(args[i+1], immediate)
        if len(result):
            result += '\n'
    return result

class Namer:
    def __init__(self):
        self.numbers = collections.defaultdict(int)

    def name(self, component_type='c'):
        self.numbers[component_type] += 1
        if self.numbers[component_type] == 1:
            return component_type
        return '{}{}'.format(component_type, self.numbers[component_type])
_namer = Namer()

class Skeleton:
    def __init__(self):
        self.lib = obvious.load_lib('Skeleton')
        obvious.set_ffi_types(self.lib.dlalRequest, str, str, bool)
        obvious.python_3_string_prep(self.lib)

    def _call(self, immediate, *args, sep=' ', detach=False):
        def convert(x):
            if isinstance(x, Component):
                return x.component
            return str(x)
        request = sep.join([convert(i) for i in args])
        if immediate:
            return report(self.lib.dlalRequest(request, True))
        elif detach:
            return report(self.lib.dlalRequest(request, False))
        else:
            self.pump()
            request_number = self.lib.dlalRequest(request, False)
            time.sleep(0.1)
            r=self.pump(request_number)
            return r

    def pump(self, request_number = None):
        for i in range(512):
            r = self.system_report(True)
            if r.startswith('value: '): r = r[7:]
            if not r:
                break
            if request_number is not None and r.startswith('{}:'.format(request_number)):
                return r.split(': ', 1)[1]
            report(r)

    def test(self):
        return self._call(True, 'test')

    def system_build(self):
        return self._call(True, 'system/build')

    def system_switch(self, system):
        return self._call(True, 'system/switch', system)

    def system_demolish(self, system):
        return self._call(True, 'system/demolish', system)

    def system_report(self, immediate):
        return self._call(immediate, 'system/report')

    def variable_get_all(self, immediate):
        return self._call(immediate, 'variable/get')

    def variable_get(self, immediate, name):
        return self._call(immediate, 'variable/get', name)

    def variable_set(self, immediate, name, value):
        return self._call(immediate, 'variable/set', name, value, sep='\n')

    def component_get_all(self, immediate):
        return self._call(immediate, 'component/get')

    def component_get(self, immediate, name):
        return self._call(immediate, 'component/get', name)

    def component_get_connections(self, immediate):
        return self._call(immediate, 'component/get/connections')

    def component_add(self, immediate, c, slot):
        return self._call(immediate, 'component/add', c, slot)

    def component_connect(self, immediate, a, b):
        return self._call(immediate, 'component/connect', a, b)

    def component_disconnect(self, immediate, a, b):
        return self._call(immediate, 'component/disconnect', a, b)

    def component_command(self, c, immediate, *command, detach=False):
        return self._call(immediate, 'component/command', c, *command, detach=detach)

    def component_demolish(self, c):
        return self._call(True, 'component/demolish', c)
_skeleton = Skeleton()

class ReprMethod:
    def __init__(self, target, method, **kwargs):
        self.target = weakref.ref(target)
        self.method = method
        self.kwargs = kwargs

    def __repr__(self):
        return str(getattr(self.target(), self.method)(**self.kwargs))

    def __call__(self, *args, **kwargs):
        method = getattr(self.target(), self.method)
        arg_names = inspect.getargspec(method).args
        x = {k: v for k, v in self.kwargs.items() if k not in arg_names[:len(args)]}
        x.update(kwargs)
        return method(*args, **x)

class System:
    def __init__(self):
        self.system = _skeleton.system_build()
        self.switched = _skeleton.system_switch(self.system)
        self.components = {}
        self.set('sampleRate', 44100, True)
        self.set('samplesPerEvaluation', 128, True)
        self.l = ReprMethod(self, 'load', start=True)

    def __del__(self):
        _skeleton.pump()
        _skeleton.system_switch(self.switched)
        _skeleton.system_demolish(self.system)

    def __repr__(self):
        return self.diagram()

    def add(self, *args, **kwargs):
        slot = kwargs.get('slot', 0)
        immediate = kwargs.get('immediate', False)
        result = ''
        for arg in args:
            result += _skeleton.component_add(immediate, arg, slot)
            if len(result):
                result += '\n'
            name = arg.name(immediate=True)
            self.components[name] = arg
            if not hasattr(self, name):
                setattr(self, name, arg)
        return result

    def set(self, name, value, immediate=False):
        _skeleton.variable_set(immediate, name, value)

    def serialize(self):
        state = {}
        # variables
        state['variables'] = json.loads(_skeleton.variable_get_all(immediate=True))
        # components
        state['component_order'] = json.loads(_skeleton.component_get_all(immediate=True))
        state['component_types'] = {k: v.type(immediate=True) for k, v in self.components.items()}
        state['components'] = {
            k: re.sub('\n|\t', ' ', v.serialize(immediate=True))
            for k, v in self.components.items()
        }
        # connections
        state['connections'] = json.loads(_skeleton.component_get_connections(immediate=True))
        # python
        state['py'] = {
            k: v.py_serialize()
            for k, v in self.components.items()
            if hasattr(v, 'py_serialize')
        }
        #
        return json.dumps(state)

    def deserialize(self, serialized):
        state = json.loads(serialized)
        # variables
        for name, value in state['variables'].items():
            self.set(name, value, True)
        # components
        components = {}
        for name, serialized in state['components'].items():
            component = component_builder(state['component_types'][name])(name=name)
            component.deserialize(serialized, immediate=True)
            components[name] = component
        for index, slot in enumerate(state['component_order']):
            for component in slot:
                component = components[component]
                self.add(component, slot=index, immediate=True)
        # connections
        for input, output in state['connections']:
            components[input].connect(components[output], immediate=True)
        # python
        for k, v in state['py'].items():
            components[k].py_deserialize(v)
        #
        return state

    def save(self, file_name='system.state.txt', extra={}):
        state = json.loads(self.serialize())
        state.update(extra)
        serialized = json.dumps(state, indent=2, sort_keys=True)
        with open(file_name, 'w') as file:
            file.write(serialized)

    def load(self, file_name='system.state.txt', start=False):
        potential_expansion = os.path.join('..', '..', 'states', file_name+'.txt')
        if os.path.exists(potential_expansion):
            file_name = potential_expansion
        with open(file_name) as file:
            state = self.deserialize(file.read())
        if start:
            self.start()
        return state

    def start(self):
        if not hasattr(self, 'audio'):
            raise Exception('no audio component')
        atexit.register(lambda: self.audio.finish())
        return self.audio.start()

    def diagram(self):
        # setup
        connections_f = {}
        connections_b = {}
        for a, b in json.loads(_skeleton.component_get_connections(immediate=True)):
            connections_f.setdefault(a, []).append(b)
            connections_b.setdefault(b, []).append(a)
        band_f = ['-']*len(self.components)
        band_b = ['-']*len(self.components)
        name_to_index = {}
        for i, k in enumerate(self.components):
            name_to_index[k] = i
        # helpers ┃ ━ ┏ ┗ ┛ ┓ ┳ ┻ ┣ ┫ ╋
        def advance():
            for band in [band_f, band_b]:
                for i, v in enumerate(band):
                    if v in '┃┏┓┳┣┫╋':
                        band[i] = '┃'
                    else:
                        band[i] = '-'
        def lay_f(index):
            if band_f[index] == '┃':
                band_f[index] = '┣'
            elif band_f[index] == '-':
                band_f[index] = '┏'
        def receive_f(index):
            band_f[index] = '┗'
        def lay_b(index):
            if band_b[index] == '┃':
                band_b[index] = '┫'
            elif band_b[index] == '-':
                band_b[index] = '┓'
        def receive_b(index):
            band_b[index] = '┛'
        def above(index, component_name):
            return index < name_to_index[component_name]
        def below(index, component_name):
            return index > name_to_index[component_name]
        # loop
        result = []
        max_len = str(max(len(i) for i in self.components))
        component_format = '{:-<' + max_len + '.' + max_len + '}'
        for index, name in enumerate(self.components):
            advance()
            # forward connections
            for i in connections_f.get(name, []):
                if above(index, i):
                    lay_f(name_to_index[i])
            if any(below(index, i) for i in connections_b.get(name, [])):
                receive_f(index)
            result.append(''.join(band_f))
            # component
            result.append(component_format.format(name))
            # backward connections
            for i in connections_b.get(name, []):
                if above(index, i):
                    lay_b(name_to_index[i])
            if any(below(index, i) for i in connections_f.get(name, [])):
                receive_b(index)
            result.append(''.join(band_b))
            #
            result.append('\n')
        return ''.join(result)

class Component:
    _libs = {}

    def __init__(self, component_type, name=None):
        if component_type not in Component._libs:
            lib = obvious.load_lib(camel_case(component_type))
            obvious.set_ffi_types(lib.dlalBuildComponent, str, str)
            obvious.python_3_string_prep(lib)
            Component._libs[component_type] = lib
        self.component = Component._libs[component_type].dlalBuildComponent(
            name or _namer.name(component_type)
        )
        commands = [i.split()[0] for i in self.command('help', immediate=True).split('\n')[1:] if len(i)]
        weak_self = weakref.ref(self)
        def captain(command):
            return lambda *args, **kwargs: weak_self().command(
                *([command]+list(args)),
                immediate=kwargs.get('immediate', False)
            )
        for command in commands:
            if command not in dir(self):
                setattr(self, command, captain(command))

    def __del__(self):
        _skeleton.component_demolish(self)

    def command(self, *command, immediate=False, detach=False):
        return _skeleton.component_command(self, immediate, *command, detach=detach)

    def connect(self, output, immediate=False):
        return _skeleton.component_connect(immediate, self, output)

    def disconnect(self, output, immediate=False):
        return _skeleton.component_disconnect(immediate, self, output)

    def phase(self): return int(self.periodic_get().split()[1])

    def period(self): return int(self.periodic_get().split()[0])

    def periodic_match(self, other, immediate=False):
        return self.command('periodic_match', other.periodic(immediate=True), immediate=immediate)

component_types = {}
def inform_component_type(name, value): component_types[snake_case(name)] = value

def component_builder(component_type):
    cls = component_types.get(component_type)
    if cls:
        return cls
    return lambda **kwargs: Component(component_type, **kwargs)

def test(): _skeleton.test()

def regularize_component_constructors(globals):
    component_dirs = sorted(os.listdir(os.path.join(root, 'components')))
    for i in component_dirs:
        if not component_types.get(i):
            globals[i.capitalize()] = functools.partial(Component, i)
