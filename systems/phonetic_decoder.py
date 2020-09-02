#===== imports =====#
import dlal

from scipy import signal

import argparse
import glob
import json
import math
import os
import re
import time

#===== args =====#
parser = argparse.ArgumentParser(description=
    'Takes phonetic parameters as produced by phonetic_encoder.py, '
    'and synthesizes a sound.'
)
parser.add_argument('--phonetic_file_path', default='assets/phonetics')
parser.add_argument('--phonetics')
parser.add_argument('--plot', choices=['irs', 'spectra', 'pole-zero'])
args = parser.parse_args()

#===== consts =====#
SAMPLE_RATE = 44100

#===== speech params =====#
phonetics = {}
for path in glob.glob(os.path.join(args.phonetic_file_path, '*.phonetic.json')):
    phonetic = os.path.basename(path).split('.')[0]
    with open(path) as file:
        phonetics[phonetic] = json.loads(file.read())

def iir_become_phonetic(iir, phonetic, smooth=None):
    p = []
    for i in phonetic['poles']:
        p.append(i)
        p.append({
            're': i['re'],
            'im': -i['im'],
        })
    z = []
    for i in phonetic['zeros']:
        z.append(i)
        z.append({
            're': i['re'],
            'im': -i['im'],
        })
    kwargs = {}
    if smooth != None:
        kwargs['smooth'] = smooth
    iir.command_detach(
        'pole_zero',
        [p, z, str(phonetic['gain'])],
        kwargs,
        do_json_prep=False,
    )

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
iir = dlal.Iir()
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

iir_become_phonetic(iir, phonetics['0'])

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
            FAST = 0.5
            SLOW = 0.9
            if any([
                say_one.phonetic == '0',  # starting from silence
                phonetics[phonetic].get('type') == 'stop',  # moving to stop
                phonetics[say_one.phonetic].get('type') == 'stop',  # moving from stop
            ]):
                c = FAST
            else:  # moving between continuants
                c = SLOW
            say_one.tone_amp = hysteresis(say_one.tone_amp, frame['tone_amp'], FAST)
            say_one.noise_amp = hysteresis(say_one.noise_amp, frame['noise_amp'], FAST)
            tone_gain.command_detach('set', [say_one.tone_amp])
            noise_gain.command_detach('set', [say_one.noise_amp / 10])  # noise is ~100x more powerful than a 100Hz impulse train
            iir_become_phonetic(iir, frame, c)
            time.sleep(0.003)
    say_one.phonetic = phonetic
say_one.phonetic = '0'

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

def say_sentence(sentence):
    pronunciations = {
        'a': 'u',
        'about': 'ubuwt',
        'all': 'al',
        'also': 'olsow',
        'as': '[ae]z',
        'be': 'by',
        'because': 'bykuz',
        'by': 'bay',
        'day': 'dey',
        'do': 'dw',
        'find': 'fuynd',
        'give': 'giv',
        'go': 'gow',
        'have': 'h[ae]v',
        'how': 'h[ae]w',
        'he': 'hy',
        'her': 'hr',
        'his': 'hiz',
        'i': 'uy',
        'into': 'intw',
        'know': 'now',
        'many': 'meny',
        'me': 'my',
        'my': 'may',
        'new': 'nyw',
        'now': 'n[ae]w',
        'of': 'uv',
        'on': 'an',
        'one': 'wun',
        'other': 'u[th_v]r',
        'our': '[ae]wr',
        'out': 'uwt',
        'people': 'pypl',
        'she': '[sh]y',
        'there': '[th_v]er',
        'their': '[th_v]er',
        'to': 'tw',
        'two': 'tw',
        'want': 'want',
        'was': 'wuz',
        'way': 'wey',
        'we': 'wy',
        'what': 'wut',
        'who': 'hw',
        'year': 'yr',
        'your': 'yor',
    }
    words = sentence.split()
    for word in words:
        if word.startswith('['):
            word = word[1:-1]
        else:
            word.lower()
            word = re.sub(r'''['.,"]''', '', word)
            if word in pronunciations:
                word = pronunciations[word]
            else:
                word = word.replace('ould', '[uu]d')
                word = word.replace('ake', 'eyk')
                word = word.replace('ere', 'yr')
                word = word.replace('ese', 'yz')
                word = word.replace('fir', 'fr')
                word = word.replace('ike', 'uyk')
                word = word.replace('ime', 'uym')
                word = word.replace('ome', 'um')
                word = word.replace('ook', '[uu]k')
                word = word.replace('ore', 'or')
                word = word.replace('thi', '[th]i')
                word = word.replace('ay', 'ey')
                word = word.replace('ch', '[ch]')
                word = word.replace('ck', 'k')
                word = word.replace('ee', 'y')
                word = word.replace('ll', 'l')
                word = word.replace('om', 'um')
                word = word.replace('oo', 'w')
                word = word.replace('ou', 'w')
                word = word.replace('ng', '[ng]')
                word = word.replace('nk', '[ng]k')
                word = word.replace('sh', '[sh]')
                word = word.replace('wh', 'w')
                word = re.sub('th[aey]', '[th_v]', word)
                word = word.replace('a', '[ae]')
                word = word.replace('c', 'k')
        print(word)
        say(word)

def tell_story():
    say_sentence('''
        [wuns] upon a time,
        there was a man,
        a [beys] man
    ''')

if args.plot:
    import dansplotcore
    if args.plot == 'pole-zero':
        plot = dansplotcore.Plot(
            transform=dansplotcore.transforms.Grid(3, 2, 6),
            hide_axes=True,
        )
        for k, v in sorted(phonetics.items()):
            if v.get('type', 'continuant') == 'continuant' and k != '0':
                plot.text(k, **plot.transform(0, 0, 0, plot.series))
                for i, u in enumerate(v['poles']):
                    t = plot.transform(u['re'], u['im'], 0, plot.series)
                    z = plot.transform(0, 0.1*i, 0, plot.series)
                    plot.line(xi=z['x'], yi=z['y'], xf=t['x'], yf=t['y'], r=0, g=255, b=0)
                for i, u in enumerate(v['zeros']):
                    t = plot.transform(u['re'], u['im'], 0, plot.series)
                    z = plot.transform(0, 0.1*i, 0, plot.series)
                    plot.line(xi=z['x'], yi=z['y'], xf=t['x'], yf=t['y'], r=255, g=0, b=0)
                unit_half = []
                for theta in range(100):
                    t = plot.transform(
                        math.cos(math.pi * theta / 100),
                        math.sin(math.pi * theta / 100),
                        0,
                        plot.series,
                    )
                    unit_half.append((t['x'], t['y']))
                for i in range(len(unit_half) - 1):
                    plot.line(
                        xi=unit_half[i+0][0],
                        yi=unit_half[i+0][1],
                        xf=unit_half[i+1][0],
                        yf=unit_half[i+1][1],
                        r=0, g=0, b=255,
                    )
                plot.series += 1
    else:
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
                iir_become_phonetic(v)
                if args.plot == 'spectra':
                    plot.plot(dlal.frequency_response(mix_buf, mix_buf, audio))
                else:
                    plot.plot(dlal.impulse_response(mix_buf, mix_buf, audio))
                iir_become_phonetic(phonetics['0'])
                audio.run()
    plot.show()
else:
    tone.midi([0x90, 40, 0x7f])
    noise.midi([0x90, 60, 0x7f])
    dlal.typical_setup()
    if args.phonetics:
        tape.to_file_i16le_start()
        say(args.phonetics)
        tape.to_file_i16le_stop()
