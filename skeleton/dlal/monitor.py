from ._component import Component

class Monitor(Component):
    def __init__(self, **kwargs):
        Component.__init__(self, 'monitor', **kwargs)

    def sample(self, name):
        self.sample_start()
        print('Enter')
        print('nothing: to exclude a second')
        print('E      : to end the sample (one second will be excluded)')
        while True:
            i = input()
            if i == '':
                print('Excluding a second.')
                self.sample_exclude()
            elif i == 'E':
                break
        self.sample_end(name)
        print(f'Ended sample "{name}".')
