import dlal

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('left_path')
parser.add_argument('right_path')
parser.add_argument('out_path')
args = parser.parse_args()

dlal.sound.flac_to_flac_stereo(
    args.left_path,
    args.right_path,
    args.out_path,
)
