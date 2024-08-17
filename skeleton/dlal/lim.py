from ._component import Component

class Lim(Component):
    def __init__(self, hard=None, soft=None, soft_gain=None, name=None):
        Component.__init__(self, 'lim', name)
        if hard != None: self.command_immediate('hard', [hard])
        if soft != None: self.command_immediate('soft', [soft])
        if soft_gain != None: self.command_immediate('soft_gain', [soft_gain])

    def __str__(self):
        hard = self.hard()
        soft = self.soft()
        soft_gain = self.soft_gain()
        if soft >= hard:
            return f'{self.name}({hard:.2f})'
        else:
            return f'{self.name}({hard:.2f}, {soft:.2f}, {soft_gain:.2f})'
