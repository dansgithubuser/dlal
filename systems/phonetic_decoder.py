#===== imports =====#
import dlal

import argparse
import glob
import json
import os
import time

#===== args =====#
parser = argparse.ArgumentParser(description=
    'Takes phonetic parameters as produced by phonetic_encoder.py, '
    'and synthesizes a sound.'
)
parser.add_argument('--phonetic_file_path', default='assets/phonetics')
parser.add_argument('--phonetics', default='helo [oo]rld')
args = parser.parse_args()

#===== consts =====#
SAMPLE_RATE = 44100

#===== speech params =====#
phonetics = {}
for path in glob.glob(os.path.join(args.phonetic_file_path, '*.phonetic.json')):
    phonetic = os.path.basename(path).split('.')[0]
    with open(path) as file:
        phonetics[phonetic] = json.loads(file.read())

#===== system =====#
audio = dlal.Audio()
dlal.driver_set(audio)
comm = dlal.Comm()
tone = dlal.Train(name='tone')
tone_gain = dlal.Gain(0, name='tone_gain')
tone_buf = dlal.Buf(name='tone_buf')
noise = dlal.Osc('noise', name='noise')
noise_gain = dlal.Gain(0, name='noise_gain')
noise_buf = dlal.Buf(name='noise_buf')
fir = dlal.Fir()
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

#===== main =====#
def say_phonetic(phonetic):
    if phonetic == ' ':
        params = {}
        frames = [{
            'tone_amp': 0,
            'noise_amp': 0,
            'fir': [0]*64,
        }]
    else:
        params = phonetics[phonetic]
        if params.get('type') in [None, 'continuant']:
            frames = [params]
        elif params['type'] == 'stop':
            frames = params['frames']

    ir = [0]*64
    tone_amp = 0
    noise_amp = 0

    def hysteresis(curr, dst):
        c = 0.5
        return c * curr + (1 - c) * dst

    duration = params.get('duration', SAMPLE_RATE / 8)
    for frame in frames:
        frame_start = time.time()
        while time.time() - frame_start < duration / SAMPLE_RATE / len(frames):
            tone_amp = hysteresis(tone_amp, frame['tone_amp'])
            noise_amp = hysteresis(noise_amp, frame['noise_amp'])
            ir = [hysteresis(curr, dst) for curr, dst in zip(ir, frame['fir'])]
            tone_gain.command_detach('set', [tone_amp])
            noise_gain.command_detach('set', [noise_amp / 4])
            fir.command_detach('ir', ir)
            time.sleep(0.003)

def say_phonetics(phonetics):
    phonetics += ' '
    i = 0
    while i < len(phonetics):
        if phonetics[i] == '[':
            i += 1
            phonetic = ''
            while phonetics[i] != ']':
                phonetic += phonetics[i]
                i += 1
        else:
            phonetic = phonetics[i]
        i += 1
        say_phonetic(phonetic)

dlal.typical_setup()
say_phonetics(args.phonetics)
