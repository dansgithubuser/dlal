from ._default_components import *
from ._logging import get_logger_names, set_logger_level
from ._server import serve
from ._skeleton import *

from . import _utils

import os as _os

[
    exec(f'from .{i} import {_utils.snake_to_upper_camel_case(i)}', globals())
    for i in component_kinds(special=True)
]

if _os.environ.get('DLAL_LOG_LEVEL'):
    set_logger_level('dlal', _os.environ['DLAL_LOG_LEVEL'])
