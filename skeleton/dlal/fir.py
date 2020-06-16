from ._component import Component

class Fir(Component):
    def __init__(self, ir=None, name=None):
        Component.__init__(self, 'fir', name)
        from ._skeleton import Immediate
        with Immediate():
            if ir != None: self.ir(ir)

    def ir(self, ir):
        return self.command('ir', [ir], do_json_prep=False)
