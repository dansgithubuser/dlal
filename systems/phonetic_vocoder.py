import argparse
import json
import math
import os

parser = argparse.ArgumentParser()
parser.add_argument('recording_path')
args = parser.parse_args()

os.environ['PHONETIC_ENCODER_RECORDING_PATH'] = args.recording_path
import dlal
import phonetic_encoder as pe
dlal.comm_set(None)
import phonetic_decoder as pd

run_size = pe.audio.run_size()
duration = pe.filea.duration()
samples = 0
file = open('phonetic_vocoder.i16le', 'wb')

while samples < duration:
    pe.audio.run()
    sample = pe.sample_system()
    params = pe.parameterize(*sample)
    frame = pe.frames_from_params([params])[0]
    amp = min(params['f'] * 10, 1)
    pd.synth.synthesize(
        [amp * i[0] for i in frame['tone']['spectrum']],
        [amp * i[0] for i in frame['noise']['spectrum']],
        frame['toniness'][0],
        0,
    )
    pd.audio.run()
    pd.tape.to_file_i16le(file)
    samples += run_size
