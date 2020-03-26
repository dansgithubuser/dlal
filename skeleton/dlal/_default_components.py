from ._component import Component, COMPONENTS_DIR
from ._utils import snake_to_upper_camel_case

import os

DIR = os.path.dirname(os.path.realpath(__file__))
SPECIAL_COMPONENTS = [i[:-3] for i in os.listdir(DIR)]

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
