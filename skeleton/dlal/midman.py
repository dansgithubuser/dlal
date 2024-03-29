from ._component import Component

import json

class Midman(Component):
    def __init__(self, directives=[], **kwargs):
        Component.__init__(self, 'midman', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            for i in directives:
                self.directive(*i)

    def directive(self, pattern, component, name, *args, **kwargs):
        return self.command('directive', [
            pattern,
            component,
            json.dumps({
                'name': name,
                'args': args,
                'kwargs': kwargs,
            })
        ])
