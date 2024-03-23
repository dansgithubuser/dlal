'''This file contains high-level logic associated with
- information outside systems
- the system
- all components
It serves as an interface to such logic.'''

from ._component import Component as _Component, component_kinds
from ._server import audio_broadcast_start, serve
from ._utils import (
    snake_to_upper_camel_case as _snake_to_upper_camel_case,
    iterable as _iterable,
)

import midi

import json as _json
import math as _math
import re as _re

class _Default: pass

def driver_set(driver):
    'Setting a driver causes components to be added to it when they are constructed.'
    result = _Component._driver
    _Component._driver = driver
    return result

def comm_set(comm):
    'Setting a comm causes components to use it to queue commands.'
    _Component._comm = comm

class Immediate:
    def __enter__(self):
        self.comm = _Component._comm
        _Component._comm = None

    def __exit__(self, *args):
        _Component._comm = self.comm

class Detach:
    def __enter__(self):
        self.prev = _Component._detach
        _Component._detach = True

    def __exit__(self, *args):
        _Component._detach = self.prev

def component(name, default=_Default):
    if default == _Default:
        return _Component._components[name]
    else:
        return _Component._components.get(name, default)

def component_class(kind):
    class_name = _snake_to_upper_camel_case(kind)
    locals = {}
    exec(f'from . import {class_name} as result', globals(), locals)
    return locals['result']

def connect(*args, _dis=False):
    '''\
    Terse connection function.
    This function is best described as a set of rules that can be composed to create a concise structure.

    Arguments can be components or subsystems:
    - `connect(a, b)` is equivalent to `a.connect(b)`
        - if `a` is a subsystem, `a.connect_outputs(b)`
        - if `b` is a subsystem, `b.connect_inputs(a)`

    Arguments are connected left to right:
    - `connect(*a)` is _like_ `for i, j in zip(a, a[1:]): connect(i, j)`
        - equivalent to `connect(a[0]); for i, j in zip(a, a[1:]): connect(primary(i, 'o'), j)`

    `primary(a, x)` is equal to `a` for components and subsystems.

    Lists are fully connected; tuples are connected component-wise:
    - `connect(*a, [*b], *c)` is _like_ `for i in b: connect(*a, i, *c)`
        - equivalent to `connect(*a); connect(*c); for i in b: connect(primary(a[-1], 'o'), i, primary(c[0], 'i'))`
    - `connect(*a, (*b,), (*c,), *d)` is _like_ `for i, j in zip(b, c): connect(a, i, j, d)`
        - equivalent to `connect(*a); connect(*d); for i, j in zip(b, c): connect(primary(a[-1], 'o'), i, j, primary(d[0], 'i'))`

    `primary([*a], x)` is equal to `[*primary(i, x) for i in a]`.
    `primary((*a,), x)` is equal to `tuple(primary([*a], x))`.

    Structure can be nested:
    - `connect(*a, [*b, '+>', *c], *d)` is equivalent to:
        - `connect(primary(b, 'o')[-1], primary(c, 'i')[0])` arrow
        - `connect(*c)` nested structure
        - `connect(*a, b, *d)` like a list (works with tuples as well)
    - `connect(*a, [*b, '<+', *c], *d)` is equivalent to:
        - `connect(primary(c, 'o')[0], primary(b, 'i')[-1])` arrow
        - `connect(*c[::-1])` nested structure
        - `connect(*a, b, *d)` like a list (works with tuples as well)
    - `connect(*a, [*b, '>', *c], *d)` is equivalent to:
        - `connect(primary(b, 'o')[-1], primary(c, 'i')[0])` arrow
        - `connect(*c)` nested structure
        - `connect(*a, b, [], *d)` like a list with a break on right (works with tuples as well)
    - `connect(*a, [*b, '<', *c], *d)` is equivalent to:
        - `connect(primary(c, 'o')[0], primary(b, 'i')[-1])` arrow
        - `connect(*c[::-1])` nested structure
        - `connect(*a, [], b, *d)` like a list with a break on left (works with tuples as well)

    Multiple arrows can be used:
    - `connect(*a, [*b, arrow1, *c, arrow2, *d], *e)` is _like_ `connect(*a, [*b, arrow1, *c], *e); connect(*a, [*b, arrow2, *d], *e)`
        - equivalent to:
            - `connect(a, [*b, arrow1, *c], e)`
            - `connect([primary(b, 'o')[-1], arrow2, *d])`

    `primary([*a, '>', *b], 'o')` is equal to `[]`.
    `primary((*a, '<', *b), 'i')` is equal to `[]`.
    `primary([*a, arrow, *b], x)` is equal to `primary([*a], x)`.
    `primary((*a, arrow, *b), x)` is equal to `primary((*a,), x)`.

    For example:
    ```
    connect(
        a,
        [
            b,
            [c, '>', d],
        ],
        [e, '<+', d],
        f,
    )
    ```
    is equivalent to
    ```
    connect(primary(               a), [b, [c, '>', d]])
    connect(primary([b, [c, '>', d]]), [e, '<+', d]    )
    connect(primary(    [e, '<+', d]), f               )
    ```
    is equivalent to
    ```
    connect(a, b)
    connect(a, [c, '>', d])

    connect([e, '<+', d])
    connect(b, e)
    - `connect(*a, [*b], *c)` is _like_ `for i in b: connect(*a, i, *c)`
        - equivalent to `connect(*a); connect(*c); for i in b: connect(primary(a[-1], 'o'), i, primary(c[0], 'i'))`

    connect(e, f)
    ```
    is equivalent to
    ```
    connect(a, b)
    connect(c, d); connect(a, c)

    connect(d, e)
    connect(b, e)

    connect(e, f)
    ```
    which looks like
    ```
    a -+-> b ------+-> e -> f
       +-> c -> d -+
    ```
    '''

    def connect_agnostic(a, b):
        from ._subsystem import Subsystem
        if not isinstance(a, _Component) and not isinstance(a, Subsystem):
            if not _dis:
                raise Exception(f'not sure how to connect {a}')
            else:
                raise Exception(f'not sure how to disconnect {a}')
        if not isinstance(b, _Component) and not isinstance(b, Subsystem):
            if not _dis:
                raise Exception(f'not sure how to connect to {b}')
            else:
                raise Exception(f'not sure how to disconnect from {b}')
        if isinstance(a, _Component):
            if isinstance(b, _Component):
                if not _dis:
                    a.connect(b)
                else:
                    a.disconnect(b)
            elif isinstance(b, Subsystem):
                if not _dis:
                    b.connect_inputs(a)
                else:
                    b.disconnect_inputs(a)
        elif isinstance(a, Subsystem):
            if isinstance(b, _Component):
                if not _dis:
                    a.connect_outputs(b)
                else:
                    a.disconnect_outputs(b)
            elif isinstance(b, Subsystem):
                if not _dis:
                    connect(a.outputs, b.inputs)
                else:
                    connect(a.outputs, b.inputs, _dis=True)

    def primary(arg, x=None):
        if type(arg) == list:
            result = []
            for i in arg:
                if type(i) == str:
                    if (i, x) == ('>', 'o'): return []
                    if (i, x) == ('<', 'i'): return []
                    break
                result.extend(primary(i, x))
            return result
        elif type(arg) == tuple:
            return tuple(primary(list(arg), x))
        else:
            return [arg]

    def connect_arrow(last_primary, stack, arrow):
        if '>' in arrow:
            connect(primary(last_primary, 'o'), *stack)
        else:
            connect(*stack[::-1], primary(last_primary, 'i'))

    if len(args) == 0:
        return
    elif len(args) == 1:
        arg = args[0]
        if not _iterable(arg): return
        prev = None
        last_primary = None
        arrow = None
        stack = []
        for i in arg:
            if type(i) == str:
                if last_primary == None:
                    last_primary = prev
                    connect(last_primary)
                else:
                    connect_arrow(last_primary, stack, arrow)
                    stack = []
                arrow = i
            elif last_primary != None:
                stack.append(i)
            prev = i
        if arrow:
            connect_arrow(last_primary, stack, arrow)
        for i in arg:
            if type(i) == str: break
            connect(i)
    elif len(args) == 2:
        src, dst = args
        if not _iterable(src) and not _iterable(dst):
            connect_agnostic(src, dst)
        else:
            if type(src) == tuple and type(dst) == tuple:
                for i, j in zip(primary(src, 'o'), primary(dst, 'i')):
                    connect(i, j)
            else:
                for i in primary(src, 'o'):
                    for j in primary(dst, 'i'):
                        connect(i, j)
            connect(src)
            connect(dst)
    else:
        connect(args[0])
        for i, j in zip(args, args[1:]):
            connect(primary(i, 'o'), j)

def disconnect(*args):
    '''Terse disconnection function. Like `connect` but disconnects.
    Useful for agnostic disconnection more than for disconnecting complex structures.'''
    connect(*args, _dis=True)

def typical_setup(*, live=True, duration=None, out_path='out.i16le'):
    import atexit
    import os
    audio = component('audio', None)
    comm = component('comm', None)
    tape = component('tape', None)
    if live:
        if audio:
            audio.start()
            atexit.register(lambda: audio.stop())
        if comm:
            comm_set(comm)
        serve()
    else:
        assert tape
        assert audio
        assert duration
        runs = int(duration * audio.sample_rate() / audio.run_size())
        n = tape.size() // audio.run_size()
        with open(out_path, 'wb') as file:
            for i in range(runs):
                audio.run()
                if i % n == n - 1 or i == runs - 1: tape.to_file_i16le(file)
                print(f'{100*(i+1)/runs:5.1f} %', end='\r')
            print()

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
    # helpers; char set: ┈ │ ━ ┏ ┗ ┛ ┓ ┳ ┻ ┣ ┫ ╋
    def advance():
        for band in [band_f, band_b]:
            for i, v in enumerate(band):
                if v in '│┏┓┳┣┫╋':
                    band[i] = '│'
                else:
                    band[i] = '┈'
    def lay_f(index):
        if band_f[index] == '│':
            band_f[index] = '┣'
        elif band_f[index] == '┈':
            band_f[index] = '┏'
    def receive_f(index):
        band_f[index] = '┗'
    def lay_b(index):
        if band_b[index] == '│':
            band_b[index] = '┫'
        elif band_b[index] == '┈':
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
    component_format = '[{:-<' + max_len + '.' + max_len + '}]'
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
        for connectee, extra in connectees.items():
            component.connect(namespace[connectee], **extra)

def impulse_response(ci, co, driver=None):
    if driver == None: driver = _Component._driver
    from . import Train
    from . import Tape
    with driver:
        train = Train(name='dlal.impulse_response.train', slot=1)
        train.connect(ci)
        train.one()
        tape = Tape(name='dlal.impulse_response.tape')
        co.connect(tape)
        ir = []
        for i in range(64):
            driver.run()
            ir.extend(tape.read())
        train.disconnect(ci)
        co.disconnect(tape)
    train.__del__()
    tape.__del__()
    return ir

def frequency_response(ci, co, driver=None, n=64, settling_time=0.01):
    if driver == None: driver = _Component._driver
    from . import Osc
    from . import Tape
    settling_runs = int(settling_time * driver.sample_rate() / driver.run_size())
    with driver:
        osc = Osc(name='dlal.frequency_response.osc', slot=1)
        osc.connect(ci)
        tape = Tape(name='dlal.frequency_response.tape')
        co.connect(tape)
        fr = []
        for i in range(n):
            freq = (driver.sample_rate() / 2) ** (i / n)
            osc.freq(freq)
            peak = 0
            for _ in range(settling_runs):
                driver.run()
                peak = max([abs(i) for i in tape.read()] + [peak])
            fr.append((freq, 20 * _math.log10(peak)))
            for _ in range(settling_runs):
                driver.run()
                tape.read()
        osc.disconnect(ci)
        co.disconnect(tape)
    osc.__del__()
    tape.__del__()
    return fr
