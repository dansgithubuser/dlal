'''This file contains high-level logic associated with
- information outside systems
- the system
- all components
It serves as an interface to such logic.'''

from ._component import Component as _Component, component_kinds
from ._server import audio_broadcast_start, serve
from ._utils import snake_to_upper_camel_case

import midi

import json as _json

class _Default: pass

def driver_set(driver):
    _Component._driver = driver

def queue_set(comm):
    _Component._comm = comm

class Immediate:
    def __enter__(self):
        self.comm = _Component._comm
        _Component._comm = None

    def __exit__(self, *args):
        _Component._comm = self.comm

def component(name, default=_Default):
    if default == _Default:
        return _Component._components[name]
    else:
        return _Component._components.get(name, default)

def component_class(kind):
    class_name = snake_to_upper_camel_case(kind)
    locals = {}
    exec(f'from . import {class_name} as result', globals(), locals)
    return locals['result']

def connect(*instructions):
    '''\
    Terse connection function.

    Each instruction can be a component or a list.
    Components or lists of components are fully connected from left to right.

    For example,
    `connect(a, b, [c, d], [e, f], g)` connects
    - `a` to `b`
    - `b` to `c` and `d`
    - `c` to `e` and `f`
    - `d` to `e` and `f`
    - `e` to `g`
    - `f` to `g`

    Lists may also contain special instruction strings (SISs).
    Components that are listed in an instruction _before_ any SISs are "primary".
    Primary components are fully connected from left to right.

    `'>'` connects the last primary component to the following component; components are connected left to right thereafter.
    `'<'` connects the next component to the last primary component; components are connected right to left thereafter.

    For example,
    ```
    connect(
        [a,
            '>', b, c,
            '>', d,
        ],
        [e, f,
            '<', c,
            '<', d,
        ],
    )
    ```
    connects
    - `a` to `b` and `b` to `c`
    - `a` to `d`
    - `a` to `e` and `f`
    - `c` to `f`
    - `d` to `f`
    '''
    instr_prev = None
    for instr in instructions:
        # normalize instruction type
        if type(instr) != list: instr = [instr]
        # special instructions
        last_primary = None
        i = 0
        while i < len(instr):
            if instr[i] == '>':
                i += 1
                last_primary.connect(instr[i])
                i += 1
                while i < len(instr) and isinstance(instr[i], _Component):
                    instr[i-1].connect(instr[i])
                    i += 1
            elif instr[i] == '<':
                i += 1
                instr[i].connect(last_primary)
                i += 1
                while i < len(instr) and isinstance(instr[i], _Component):
                    instr[i].connect(instr[i-1])
                    i += 1
            else:
                last_primary = instr[i]
                i += 1
        # connect all primary components in previous instruction
        # to all primary components in current instruction
        if instr_prev:
            for src in instr_prev:
                if not isinstance(src, _Component): break
                for dst in instr:
                    if not isinstance(dst, _Component): break
                    src.connect(dst)
        # prep for next
        instr_prev = instr

def typical_setup():
    import atexit
    import os
    audio = component('audio', None)
    comm = component('comm', None)
    tape = component('tape', None)
    if tape and 'DLAL_TO_FILE' in os.environ:
        samples_per_evaluation = 64
        sample_rate = 44100
        if audio:
            samples_per_evaluation = audio.samples_per_evaluation()
            sample_rate = audio.sample_rate()
        duration = float(os.environ['DLAL_TO_FILE'])
        runs = int(duration * sample_rate / samples_per_evaluation)
        with open('out.raw', 'wb') as file:
            for i in range(runs):
                audio.run()
                tape.to_file_i16le(samples_per_evaluation, file)
    else:
        if audio:
            audio.start()
            atexit.register(lambda: audio.stop())
        if comm:
            queue_set(comm)
        serve()

def system_info():
    return {
        'components': {
            name: {'kind': component.kind}
            for name, component in _Component._components.items()
        },
        'connections': _Component._connections,
    }

def system_diagram():
    components = _Component._components
    if not components: return '┅'
    # setup
    connections_f = {}
    connections_b = {}
    for a, bs in _Component._connections.items():
        for b in bs:
            connections_f.setdefault(a, []).append(b)
            connections_b.setdefault(b, []).append(a)
    band_f = ['-']*len(components)
    band_b = ['-']*len(components)
    name_to_index = {}
    for i, k in enumerate(components):
        name_to_index[k] = i
    # helpers; char set: ┅ ┃ ━ ┏ ┗ ┛ ┓ ┳ ┻ ┣ ┫ ╋
    def advance():
        for band in [band_f, band_b]:
            for i, v in enumerate(band):
                if v in '┃┏┓┳┣┫╋':
                    band[i] = '┃'
                else:
                    band[i] = '┅'
    def lay_f(index):
        if band_f[index] == '┃':
            band_f[index] = '┣'
        elif band_f[index] == '┅':
            band_f[index] = '┏'
    def receive_f(index):
        band_f[index] = '┗'
    def lay_b(index):
        if band_b[index] == '┃':
            band_b[index] = '┫'
        elif band_b[index] == '┅':
            band_b[index] = '┓'
    def receive_b(index):
        band_b[index] = '┛'
    def above(index, component_name):
        return index < name_to_index[component_name]
    def below(index, component_name):
        return index > name_to_index[component_name]
    # loop
    result = []
    max_len = str(max(len(i) for i in components))
    component_format = '[{:|<' + max_len + '.' + max_len + '}]'
    for index, name in enumerate(components):
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

def system_save(file_path):
    def call_or_none(value, member):
        if hasattr(value, member):
            return getattr(value, member)()
    def map_components(f):
        result = {}
        for name, component in _Component._components.items():
            value = f(component)
            if value: result[name] = value
        return result
    j = _json.dumps(
        {
            'component_kinds':
                map_components(lambda i: i.kind),
            'components':
                map_components(lambda i: call_or_none(i, 'to_json')),
            'cross_state':
                map_components(lambda i: call_or_none(i, 'get_cross_state')),
            'connections':
                _Component._connections,
        },
        indent=2
    )
    with open(file_path, 'w') as file: file.write(j)

def system_load(file_path, namespace):
    with open(file_path) as file: j = _json.loads(file.read())
    for name, kind in j['component_kinds'].items():
        namespace[name] = component_class(kind)(name)
    for name, component in _Component._components.items():
        jc = j['components'].get(name)
        if jc: component.from_json(jc)
    for name, component in _Component._components.items():
        jc = j['cross_state'].get(name)
        if jc: component.set_cross_state(jc)
    for name, connectees in j['connections'].items():
        component = namespace[name]
        for connectee in connectees:
            component.connect(namespace[connectee])
