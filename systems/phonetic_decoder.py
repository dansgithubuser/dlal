#===== imports =====#
import dlal

import argparse
import glob
import json
import math
import os
import random
import re
import time

#===== args =====#
parser = argparse.ArgumentParser(description=
    'Takes phonetic parameters as produced by phonetic_encoder.py, '
    'and synthesizes a sound.'
)
parser.add_argument('--phonetic-file-path', default='assets/phonetics')
parser.add_argument('--phonetics')
parser.add_argument('--tell-story', type=int)
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
def get_frames(phonetic):
    params = phonetics[phonetic]
    if params.get('type') in [None, 'continuant']:
        return [params]
    elif params['type'] == 'stop':
        return params['frames']
    raise Exception(f'''unknown phonetic type "{params['type']}"''')

def say_one(phonetic):
    if phonetic == ' ':
        phonetic = '0'
    params = phonetics[phonetic]
    frames = get_frames(phonetic)

    def hysteresis(curr, dst, c):
        return c * curr + (1 - c) * dst

    duration = params.get('duration', SAMPLE_RATE / 6)
    for frame_i, frame in enumerate(frames):
        frame_start = time.time()
        while time.time() - frame_start < duration / SAMPLE_RATE / len(frames):
            FAST = 0.7
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
            iir_become_phonetic(iir, frame, c)
            tone_gain.command_detach('set', [say_one.tone_amp])
            noise_gain.command_detach('set', [say_one.noise_amp / 10])  # noise is ~100x more powerful than a 100Hz impulse train
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
        word = re.sub(r'''['.,"]''', '', word)
        if word.startswith('['):
            word = word[1:-1]
        else:
            word = word.lower()
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

def tell_story(i=0):
    say_sentence([
        # 0
        '''
        [wuns] [upan] a time,
        there was a man,
        a [b[ay]ys] man
        ''',
        # 1
        '''
        A big [kunery] [duznt] get [[th_v]u] [wurm].
        ''',
        # 2
        '''
        [[th_v]u] [wurd] [l[ay]ydy] [iz] a [trm] [uv] [respekt] [for] a [grl] [or] [w[uu]min],
        [[th_v]u] [ekwivulent] [uv] [jentlmin].
        ''',
        # 3
        '''
        [tw[ng]kl] [tw[ng]kl] [litl] [star]
        ''',
        # 4
        '''
        [d[ay]yzy] [d[ay]yzy] [giv] [my] [yor] [[ae]nsr] [dw]
        ''',
        # 5
        '''
        [[th]in] [herz] [pruper] [for] [[th_v]u] [ok[ay]y[sh_v]in]
        ''',
        # 6
        '''
        A [[ch]yry] [jelyfi[sh]] [p[ay]ynts] too [mu[ch]].
        '''
    ][i])

def say_random():
    decompositions = {
        's': [
            ['np', 'vp'],
        ],
        'np': [
            ['n'],
            ['d', 'n'],
            ['adj', 'n'],
        ],
        'vp': [
            ['v'],
            ['v', 'np'],
            ['v', 'adv'],
            ['adv', 'v'],
        ],
        'cp': [
            ['c', 's'],
        ],
    }
    words = {
        'adj': [
            'artistik',
            'br[ae]wn',
            'kold', 'kreyzy',
            'dery[ng]g',
            'rly',
            'f[ae]st',
            'greyt',
            'hard', 'hu[ng]gry',
            'intresti[ng]g',
            'jaly',
            'nuytly',
            'litl', 'luvly', 'luky',
            'moldy', 'metl',
            'nuys',
            'old',
            'prity', 'prpl',
            'kwik',
            'red',
            'si[ng]gy[ng]g',
            'temporery',
            'unkempt',
            'v[ae]st',
            'wity',
            'yelo',
            'zamby',
        ],
        'adv': [
            'akwrdly', 'e[ng]grily',
            'bori[ng]gly', 'beysikly',
            'keri[ng]gly',
            'jrayly',
            'rly',
            'fr[ae]ntikly',
            'gler[ng]gly',
            'h[ae]pily',
            'impraprly',
            'jelusly',
            'nowy[ng]gly',
            'libruly', 'l[ae]st',
            'm[ae]nywly',
            'n[ae]stily',
            'openly',
            'praprly',
            'kwizikly',
            'rily',
            'sint[ae]ktikly', 'srtinly', 'skilf[uu]ly',
            '[ch]rw[th]f[uu]ly',
            'rjintly',
            'veygly',
            'wili[ng]gly',
            'yrni[ng]gly',
            'zelusly',
        ],
        'd': [
            'u',
            'hiz', 'hr',
            'muy',
            '[th_v]u',
            'yor',
        ],
        'n': [
            '[ae]pl', '[ae]ntytr',
            'brd', 'bujy',
            'k[ae]t', 'kunery',
            'dag',
            'elufint',
            'fery',
            'greyp',
            'hipo',
            'iglw',
            'jelyfi[sh]',
            'key[ng]gurww',
            'luyma byn',
            'm[ae]n', 'mi[ng]ks',
            'nu[th][ng]g',
            'askr',
            'pal', 'pretzul',
            'kwetzul',
            'rajr',
            's[ae]m', 'skwid',
            'tim',
            'umbrelu',
            'vyikl',
            'wumin',
            'zaylufown',
            'yeloj[ae]kit',
            'zybru',
        ],
        'v': [
            '[ae]kts',
            'kunsidrz',
            'yts',
            'left',
            'nowz',
            'red',
            'studyz', 'sed',
        ],
        'c': [
            '[ae]nd',
            'wuyl',
            'but',
            'hawevr',
        ],
    }
    tree = ['s']
    while any(i in decompositions for i in tree):
        print(tree)
        if len(tree) < 10:
            while True:
                i = random.randint(0, len(tree)-1)
                v = tree[i]
                if v in decompositions:
                    tree = tree[:i] + random.choice(decompositions[v]) + tree[i+1:]
                    break
        else:
            for i, v in enumerate(tree):
                if v in decompositions:
                    tree = tree[:i] + decompositions[v][0] + tree[i+1:]
                    break
    sentence = ' '.join(random.choice(words[i]) for i in tree)
    print(sentence)
    say(sentence)
    return sentence

if args.plot:
    import dansplotcore
    if args.plot == 'pole-zero':
        plot = dansplotcore.Plot(
            transform=dansplotcore.transforms.Grid(3, 2, 6),
            hide_axes=True,
        )
        for k, v in sorted(phonetics.items()):
            if k == '0': continue
            frames = get_frames(k)
            for frame in frames:
                plot.text(k, **plot.transform(0, 0, 0, plot.series))
                for i, u in enumerate(frame['poles']):
                    t = plot.transform(u['re'], u['im'], 0, plot.series)
                    z = plot.transform(0, 0.1*i, 0, plot.series)
                    plot.line(xi=z['x'], yi=z['y'], xf=t['x'], yf=t['y'], r=0, g=255, b=0)
                for i, u in enumerate(frame['zeros']):
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
                plot.next_series()
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
            if k == '0': continue
            frames = get_frames(k)
            for frame in frames:
                plot.text(k, **plot.transform(0, 0, 0, plot.series))
                iir_become_phonetic(iir, frame)
                if args.plot == 'spectra':
                    plot.plot(dlal.frequency_response(mix_buf, mix_buf, audio))
                else:
                    plot.plot(dlal.impulse_response(mix_buf, mix_buf, audio))
                iir_become_phonetic(iir, phonetics['0'])
                audio.run()
    plot.show()
else:
    tone.midi([0x90, 42, 0x7f])
    noise.midi([0x90, 60, 0x7f])
    dlal.typical_setup()
    if args.phonetics or type(args.tell_story) == int:
        tape.to_file_i16le_start()
        if args.phonetics:
            say(args.phonetics)
        if type(args.tell_story) == int:
            tell_story(args.tell_story)
        tape.to_file_i16le_stop()
