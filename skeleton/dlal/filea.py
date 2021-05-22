from ._component import Component

class Filea(Component):
    def __init__(self, file_path=None, **kwargs):
        Component.__init__(self, 'filea', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if file_path != None: self.open(file_path)
