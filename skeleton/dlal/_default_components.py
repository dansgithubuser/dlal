from ._component import Component, component_kinds
from ._utils import snake_to_upper_camel_case

__all__ = []
for kind in component_kinds(special=False):
    class_name = snake_to_upper_camel_case(kind)
    exec(
        f'class {class_name}(Component):\n'
        f'    def __init__(self, name=None):\n'
        f'        Component.__init__(self, "{kind}", name)\n'
    )
    __all__.append(class_name)
