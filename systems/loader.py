import dlal

import atexit
import sys

dlal.system_load(sys.argv[1], globals())
dlal.typical_setup()
