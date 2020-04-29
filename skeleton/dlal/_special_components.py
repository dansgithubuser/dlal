from . import _component
from . import _utils

[
    exec(f'from .{i} import {_utils.snake_to_upper_camel_case(i)}', globals())
    for i in _component.component_kinds(special=True)
]
