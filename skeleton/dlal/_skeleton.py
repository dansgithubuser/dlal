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

class UseComm:
    def __init__(self, comm):
        self.comm = comm

    def __enter__(self):
        self.old_comm = _Component._comm
        _Component._comm = self.comm

    def __exit__(self, *args):
        _Component._comm = self.old_comm

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

def connect(*instructions):
    '''\
    Terse connection function.

    Each instruction can be a component, list, or tuple.
    Components or lists of components are fully connected from left to right.
    Tuples of components are connected component-wise from left to right.
    Components may be subsystems.

    For example,
    `connect(a, b, [c, d], [e, f], g)` connects
    - `a` to `b`
    - `b` to `c` and `d`
    - `c` to `e` and `f`
    - `d` to `e` and `f`
    - `e` to `g`
    - `f` to `g`

    `connect((a, b), (c, d))` connects
    - `a` to `c`
    - `b` to `d`

    Lists and tuples may also contain special instruction strings (SISs).
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

    def connect_agnostic(a, b):
        from ._subsystem import Subsystem
        if isinstance(a, _Component):
            if isinstance(b, _Component):
                a.connect(b)
            elif isinstance(b, Subsystem):
                b.connect_inputs(a)
            else:
                raise Exception(f'not sure how to connect to {b}')
        elif isinstance(a, Subsystem):
            if isinstance(b, _Component):
                a.connect_outputs(b)
            else:
                raise Exception('not sure how to connect subsystem to {b}')
        else:
            raise Exception(f'not sure how to connect {a}')

    instr_prev = None
    for instr in instructions:
        # normalize instruction type
        if not _iterable(instr): instr = [instr]
        # special instructions
        last_primary = None
        i = 0
        while i < len(instr):
            if instr[i] == '>':
                i += 1
                connect_agnostic(last_primary, instr[i])
                i += 1
                while i < len(instr) and type(instr[i]) != str:
                    connect_agnostic(instr[i-1], instr[i])
                    i += 1
            elif instr[i] == '<':
                i += 1
                connect_agnostic(instr[i], last_primary)
                i += 1
                while i < len(instr) and type(instr[i]) != str:
                    connect_agnostic(instr[i], instr[i-1])
                    i += 1
            else:
                last_primary = instr[i]
                i += 1
        # primary component connections
        if instr_prev:
            if type(instr_prev) == tuple and type(instr) == tuple:
                # connect primary components in previous instruction component-wise
                # to primary components in current instruction
                for src, dst in zip(instr_prev, instr):
                    if type(src) == str or type(dst) == str: break
                    connect_agnostic(src, dst)
            else:
                # connect all primary components in previous instruction
                # to all primary components in current instruction
                for src in instr_prev:
                    if type(src) == str: break
                    for dst in instr:
                        if type(dst) == str: break
                        connect_agnostic(src, dst)
        # prep for next
        instr_prev = instr

def typical_setup():
    import atexit
    import os
    audio = component('audio', None)
    comm = component('comm', None)
    tape = component('tape', None)
    if tape and 'DLAL_TO_FILE' in os.environ and audio:
        run_size = audio.run_size()
        sample_rate = audio.sample_rate()
        duration = float(os.environ['DLAL_TO_FILE'])
        runs = int(duration * sample_rate / run_size)
        with open('out.i16le', 'wb') as file:
            for i in range(runs):
                audio.run()
                tape.to_file_i16le(run_size, file)
    else:
        if audio:
            audio.start()
            atexit.register(lambda: audio.stop())
        if comm:
            comm_set(comm)
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

def read_sound(file_path):
    import soundfile as sf
    data, sample_rate = sf.read(file_path)
    return [float(i) for i in data], sample_rate

def i16le_to_flac(i16le_file_path, flac_file_path=None):
    import soundfile as sf
    if flac_file_path == None:
        flac_file_path = _re.sub(r'\.i16le$', '', i16le_file_path) + '.flac'
    data, sample_rate = sf.read(
        i16le_file_path,
        samplerate=44100,
        channels=1,
        format='RAW',
        subtype='PCM_16',
        endian='LITTLE',
    )
    sf.write(flac_file_path, data, sample_rate, format='FLAC')

def impulse_response(ci, co, driver):
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

def frequency_response(ci, co, driver, n=64, settling_time=0.01):
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
