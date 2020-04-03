from ._component import Component, json_prep

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
    def __init__(self, name=None):
        Component.__init__(self, 'oracle', name)

    def mode(self, mode=None):
        args = []
        if mode is not None: args.append(MODE.dict[mode])
        return MODE.list[int(self.command('mode', *args))]

    def format(self, name, *args, **kwargs):
        args, kwargs = json_prep(args, kwargs)
        return self.command('format', json.dumps({
            'name': name,
            'args': args,
            'kwargs': kwargs,
        }))
