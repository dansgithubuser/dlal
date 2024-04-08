from ._component import Component

import json

class Monitor(Component):
    def __init__(self, *, format=None, known_category_cmd_rate=None, **kwargs):
        Component.__init__(self, 'monitor', **kwargs)
        if format: self.format(format[0], *format[1], **format[2])
        if known_category_cmd_rate: self.known_category_cmd_rate(known_category_cmd_rate)

    def format(self, name, *args, **kwargs):
        '''Supply the name, args, and kwargs of a command.
        This command is sent to outputs when a category is detected.
        % will be replaced with f'{timestamp}-{category}'.
        '''
        return self.command('format', [json.dumps({
            'name': name,
            'args': args,
            'kwargs': kwargs,
        })])

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
