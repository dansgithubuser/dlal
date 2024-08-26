import dlal

import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('in_path', type=Path)
args = parser.parse_args()

sound = dlal.sound.read(args.in_path)
sound.to_ogg(args.in_path.with_suffix('.ogg'))
