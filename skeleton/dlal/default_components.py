from .component import Component, COMPONENTS_DIR

import os

DIR = os.path.dirname(os.path.realpath(__file__))
SPECIAL_COMPONENTS = [i[:-3] for i in os.listdir(DIR)]

def snake_to_upper_camel_case(s):
    return ''.join(i.capitalize() for i in s.split('_'))

__all__ = []
for i in os.listdir(COMPONENTS_DIR):
    if i in SPECIAL_COMPONENTS: continue
    class_name = snake_to_upper_camel_case(i)
    exec(
        f'class {class_name}(Component):\n'
        f'    def __init__(self, name=None):\n'
        f'        Component.__init__(self, "{i}", name)\n'
    )
    __all__.append(class_name)
