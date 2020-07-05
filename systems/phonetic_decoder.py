#===== imports =====#
import dlal

import argparse
import json

parser = argparse.ArgumentParser(description=
    'Takes phonetic parameters as produced by phonetic_encoder.py, '
    'and synthesizes a sound.'
)
parser.add_argument('phonetic_file_path')
args = parser.parse_args()

with open(args.phonetic_file_path) as file:
    params = json.loads(file.read())

if params.get('type') == 'stop':
    raise Exception('unimplemented')

audio = dlal.Audio()
dlal.driver_set(audio)
tone = dlal.Train(name='tone')
tone_gain = dlal.Gain(params['tone_amp'], name='tone_gain')
tone_buf = dlal.Buf(name='tone_buf')
noise = dlal.Osc('noise', name='noise')
noise_gain = dlal.Gain(params['noise_amp']/4, name='noise_gain')
noise_buf = dlal.Buf(name='noise_buf')
fir = dlal.Fir(params['fir'])
mix_buf = dlal.Buf(name='mix_buf')

dlal.connect(
    fir,
    [mix_buf,
        '<', tone_buf, tone,
        '<', noise_buf, noise,
    ],
    audio,
    [],
    tone_gain, tone_buf,
    [],
    noise_gain, noise_buf,
)

tone.midi([0x90, 48, 0x7f])
noise.midi([0x90, 60, 0x7f])

dlal.typical_setup()
