from .audio import *
from .buffer import *
from .filea import *
from .formant import *
from .helpers import *
from .liner import *
from .markov_liner import *
from .reticulated_liner import *
from .skeleton import *
from .sonic import *

import inspect

global_items = [(k, v) for k, v in globals().items()]
for k, v in global_items:
    if inspect.isclass(v) and issubclass(v, Component):
        inform_component_type(k, v)

regularize_component_constructors(globals())
