#===== imports =====#
import dlal

import argparse
import glob
import json
import math
import os
import time

#===== args =====#
parser = argparse.ArgumentParser(description=
    'Takes phonetic parameters as produced by phonetic_encoder.py, '
    'and synthesizes a sound.'
)
parser.add_argument('--phonetic_file_path', default='assets/phonetics')
parser.add_argument('--phonetics', default='helow wrld')
parser.add_argument('--plot', choices=['irs', 'spectra'])
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
iir = dlal.Iir(a=phonetics['0']['coeffs'])
mix_buf = dlal.Buf(name='mix_buf')
tape = dlal.Tape(size=44100*5)

dlal.connect(
    iir,
    [mix_buf,
        '<', tone_buf, tone,
        '<', noise_buf, noise,
    ],
    [audio, tape],
    [],
    tone_gain, tone_buf,
    [],
    noise_gain, noise_buf,
)

#===== main =====#
def say_one(phonetic):
    if phonetic == ' ':
        phonetic = '0'
    params = phonetics[phonetic]
    if params.get('type') in [None, 'continuant']:
        frames = [params]
    elif params['type'] == 'stop':
        frames = params['frames']

    def hysteresis(curr, dst, c):
        return c * curr + (1 - c) * dst

    duration = params.get('duration', SAMPLE_RATE / 8)
    for frame_i, frame in enumerate(frames):
        frame_start = time.time()
        while time.time() - frame_start < duration / SAMPLE_RATE / len(frames):
            if say_one.phonetic == '0':  # starting from silence
                c = 0
            elif len(frames) > 1:  # stop
                c = 0
            else:  # moving between continuants
                c = 0.7
            say_one.tone_amp = hysteresis(say_one.tone_amp, frame['tone_amp'], c)
            say_one.noise_amp = hysteresis(say_one.noise_amp, frame['noise_amp'], c)
            say_one.coeffs = [
                hysteresis(curr, dst, c)
                for curr, dst
                in zip(say_one.coeffs, frame['coeffs'])
            ]
            tone_gain.command_detach('set', [say_one.tone_amp])
            noise_gain.command_detach('set', [say_one.noise_amp / 10])  # noise is ~100x more powerful than a 100Hz impulse train
            iir.command_detach('a', [say_one.coeffs], do_json_prep=False)
            time.sleep(0.003)
    say_one.phonetic = phonetic
say_one.phonetic = '0'

say_one.coeffs = phonetics['0']['coeffs']
say_one.tone_amp = phonetics['0']['tone_amp']
say_one.noise_amp = phonetics['0']['noise_amp']

def say(phonetics):
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
        say_one(phonetic)

if args.plot:
    import dansplotcore
    if args.plot == 'spectra':
        plot = dansplotcore.Plot(
            transform=dansplotcore.transforms.Grid(22050, 100, 6),
            hide_axes=True,
        )
    else:
        plot = dansplotcore.Plot(
            transform=dansplotcore.transforms.Grid(4096, 4, 6),
            hide_axes=True,
        )
    for k, v in sorted(phonetics.items()):
        if v.get('type', 'continuant') == 'continuant' and k != '0':
            plot.text(k, **plot.transform(0, 0, 0, plot.series))
            iir.a(v['coeffs'])
            if args.plot == 'spectra':
                plot.plot([
                    (f, m)
                    for f, m
                    in dlal.Iir.frequency_response(a=v['coeffs'])
                ])
            else:
                plot.plot(dlal.impulse_response(mix_buf, mix_buf, audio))
            iir.a(phonetics['0']['coeffs'])
            audio.run()
    plot.show()
else:
    tone.midi([0x90, 40, 0x7f])
    noise.midi([0x90, 60, 0x7f])
    dlal.typical_setup()
    tape.to_file_i16le_start()
    say(args.phonetics)
    tape.to_file_i16le_stop()
