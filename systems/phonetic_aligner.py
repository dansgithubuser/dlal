import dlal

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--midi', '-m', 'midi_path')
parser.add_argument('--audio', '-a', 'audio_path')
args = parser.parse_args()

liner = dlal.Liner()
