import dlal

import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-l')
parser.add_argument('--evaluations', type=int, default=1000)
args = parser.parse_known_args()

s = dlal.System()
s.load(getattr(args[0], 'l', sys.argv[1]))

filea = dlal.Filea()
s.add(filea, immediate=True)
filea.open_write('render.ogg', immediate=True)
filea.swap(s.audio, immediate=True)

s.prep()
for i in range(args[0].evaluations):
    s.evaluate()
filea.close_write()
