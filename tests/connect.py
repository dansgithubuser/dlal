import dlal
from dlal._component import Component

class Connector(Component):
    def __init__(self, name):
        self.name = name

    def __del__(self):
        pass

    def connect(self, other):
        print(f'connect {self} {other}')

    def __repr__(self):
        return str(self)

liner = Connector('liner')
a = Connector('a')
b = Connector('b')
c = Connector('c')
d = Connector('d')
mixer = Connector('mixer')

dlal.connect(
    liner,
    (
        a,
        [b, '>', c, '>'],
        d,
    ),
    mixer,
)
