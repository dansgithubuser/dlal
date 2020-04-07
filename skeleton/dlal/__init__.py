from . import _utils

import os as _os
import sys as _sys

_sys.path.append(_os.path.join(_utils.DEPS_DIR, 'dansmidilibs'))

from ._default_components import *
from ._logging import get_logger_names, set_logger_level
from ._skeleton import *

[
    exec(f'from .{i} import {_utils.snake_to_upper_camel_case(i)}', globals())
    for i in component_kinds(special=True)
]

if _os.environ.get('DLAL_LOG_LEVEL'):
    set_logger_level('dlal', _os.environ['DLAL_LOG_LEVEL'])
