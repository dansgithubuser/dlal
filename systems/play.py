import dlal

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('path')
args = parser.parse_args()

audio = dlal.Audio(driver=True)
afr = dlal.Afr(args.path)

afr.connect(audio)

dlal.typical_setup()
