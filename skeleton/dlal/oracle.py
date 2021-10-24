from ._component import Component

import json

class Mode:
    def __init__(self, *modes):
        self.list = []
        self.dict = {}
        for i, mode in enumerate(modes):
            self.list.append(mode)
            self.dict[mode] = i

MODE = Mode('f32', 'i32', 'pitch_wheel')

class Oracle(Component):
    def __init__(self, mode=None, m=None, b=None, format=None, **kwargs):
        Component.__init__(self, 'oracle', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if mode != None: self.mode(mode)
            if m != None: self.m(m)
            if b != None: self.b(b)
            if format != None: self.format(*format)

    def mode(self, mode=None):
        '''choices: ['f32', 'i32', 'pitch_wheel']'''
        args = []
        if mode is not None: args.append(MODE.dict[mode])
        return MODE.list[int(self.command('mode', args))]

    def format(self, name, *args, **kwargs):
        '''Supply the name, args, and kwargs of a command.
        Use % to represent the control voltage.
        If mode is 'pitch_wheel', use %l and %h for low and high bytes.
        '''
        return self.command('format', [json.dumps({
            'name': name,
            'args': args,
            'kwargs': kwargs,
        })])
