import dlal

import sys

liner = dlal.Liner()

liner.load(sys.argv[1], immediate=True)
dlal.typical_setup()
