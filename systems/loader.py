import dlal

import argparse
import sys

parser=argparse.ArgumentParser()
parser.add_argument('-l')
args=parser.parse_known_args()

system=dlal.System()
s=system
s.l(getattr(args[0], 'l', sys.argv[1]))
