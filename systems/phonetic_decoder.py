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
parser.add_argument('--phonetics')
parser.add_argument('--rot13', action='store_true')
parser.add_argument('--tell-story', type=int)
parser.add_argument('--create-phonetic-samples', '--cps', action='store_true')
parser.add_argument('--phonetics-path', default='assets/phonetics')
parser.add_argument('--approach', choices=['sub', 'add'], default='sub')
args = parser.parse_args()

#===== consts =====#
SAMPLE_RATE = 44100

#===== system =====#
audio = dlal.Audio()
dlal.driver_set(audio)
comm = dlal.Comm()

if args.approach == 'sub':
    tone = dlal.Train(name='tone')
    noise = dlal.Osc('noise', name='noise')
    phonetizer = dlal.subsystem.Phonetizer()
    tape = dlal.Tape(size=44100*5)

    dlal.connect(
        (tone, noise),
        (phonetizer.tone_buf, phonetizer.noise_buf),
        [],
        phonetizer,
        [audio, tape],
    )
elif args.approach == 'add':
    noise = dlal.Noisebank(0.7)
    noise_gain = dlal.Gain(8)
    tone = dlal.Sinbank(smooth=0.9)
    gain = dlal.Gain(8)
    buf = dlal.Buf()
    tape = dlal.Tape(size=44100*5)

    dlal.connect(
        [tone, noise, noise_gain, gain],
        buf,
        [audio, tape],
    )

    def say_custom(frame, wait, **kwargs):
        if frame != None:
            if 'tone_spectrum' in frame:
                tone.command_detach('spectrum', [frame['tone_spectrum']])
            else:
                tone.command_detach('spectrum', [[]])
            if 'noise_spectrum' in frame:
                noise.command_detach('spectrum', [frame['noise_spectrum']])
            else:
                noise.command_detach('spectrum', [[0] * 64])
        comm.wait(wait)

    phonetizer = dlal.subsystem.Phonetizer(say_custom=say_custom)

#===== main =====#
def say_one(phonetic_symbol):
    if phonetic_symbol == ' ':
        phonetic_symbol = '0'
    time.sleep(phonetizer.say(phonetic_symbol) / SAMPLE_RATE)

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
    if i == 9:
        d = 6400
        phonetizer.prep_syllables(
            '.[ae].[sh] .i.z f.a.l [th]r.w [th_v].u m.y n.y.[ng]',
            [
                { 'on':  2 * d, 'off':  4 * d},
                { 'on':  4 * d, 'off':  6 * d},
                { 'on':  6 * d, 'off':  8 * d },
                { 'on':  8 * d, 'off':  9 * d },
                { 'on':  9 * d, 'off': 10 * d },
                { 'on': 10 * d, 'off': 12 * d },
                { 'on': 12 * d, 'off': 14 * d },
            ],
        )
    else:
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
            [[th_v]u] [wrd] [l[ay]ydy] [iz] a [trm] [uv] [respekt] [for] a [grl] [or] [w[uu]min],
            [[th_v]u] [ekwivulent] [uv] [jentlmin].
            ''',
            # 3
            '''
            [twi[ng]kl] [twi[ng]kl] [litl] [star]
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
            ''',
            # 7
            '[[ae/2][-y]0[h/2][ae]v0u0f[ae]nsy0silwet]',  # I have a fancy silhouette
            # 8
            '[[h/2][ae/2][-w]0duz0[th_v/4]u0gr[e/2][-y]t0b[l/2][uu][-w]0k[h/2][ae]t0jump0j[ae/2][-y]v0[ae]nd0d[ae]ns0efrtlesly]',  # How does the great blue cat jump jive and dance effortlessly
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
            'artistik', 'artful',
            'br[ae]wn', 'big',
            'kold', 'kreyzy', 'kwl',
            'dery[ng]g', 'deynty',
            'rly', 'ygr',
            'f[ae]st', 'frendly', 'fym[ay]yl',
            'greyt', 'gryn',
            'hard', 'hu[ng]gry', 'hy[-w]j', 'hat',
            'intresti[ng]g', 'il',
            'jaly', 'jelus',
            'nuytly', 'keen',
            'litl', 'luvly', 'luky', 'lwd',
            'moldy', 'metl', 'molten',
            'nuys', 'norml',
            'old', 'ad', 'ornj',
            'prity', 'prpl', 'punk',
            'kwik', 'kyn',
            'red', 'ri[ch]',
            'si[ng]gy[ng]g', 'saft',
            'temporery', 'tin', '[th]in',
            'unkempt', 'ul[ch]ru',
            'v[ae]st', 'v[ae]ylet',
            'wity', 'wably',
            'zynufobik',
            'yelo', 'yu[ng]g',
            'zamby', 'zelus',
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
            'lib[r/2]uly', 'l[ae]st',
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
            '[ae]pl', '[ae]ntytr', '[ae]dult',
            'brd', 'bujy', 'b[ay]yby',
            'k[ae]t', 'kunery', 'kap',
            'dag', 'daktr',
            'elufint', '[e/2][-y]g',
            'fery', 'fi[sh]',
            'greyp', 'g[o/2][-w]st',
            'hipow', 'hors',
            'ig[l/2]w', 'it',
            'jelyfi[sh]', 'jet',
            'key[ng]gurww', 'kid',
            'luyma byn', 'lag',
            'm[ae]n', 'mi[ng]ks', 'mam',
            'nu[th][ng]g', 'nut',
            'aktup[uu]s', 'atr',
            'pretzul', 'p[ae]y', 'pe[ng]gwin',
            'kwetzul', 'kwortrb[ae]k',
            'rak',
            'skwid', 'star',
            'twrist',
            'umbrelu', 'unkl',
            'vyikl', 'vwvwzeylu', 'v[ae]yris',
            'w[uu]min', 'watr',
            'zaylufown',
            'yeloj[ae]kit',
            'zybru',
        ],
        'v': [
            '[ae]kts', 'ujust',
            'bleymz',
            '[ch]ekt', 'kunsidrz',
            'jrap[ng]g',
            'ulekt', 'yts',
            'felt', 'fed',
            'gat',
            'hit', 'held',
            '[ae]ydentifuyz',
            'joynd',
            'left', 'luvz',
            'meyks', 'meyd',
            'nowz', 'kikd',
            'nego[sh]yeyts',
            'openz',
            'pleyz',
            'kwit',
            'red', 'r[ae]ydy[ng]g', 'runz',
            'studyz', 'sed', 'spun',
            '[ch]rips', 'tips',
            'rjiz',
            'vywz',
            'wants',
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

def say_rot13(phonetics):
    def rot13(char):
        if not re.match('[a-z]', char): return char
        return chr((ord(char) - ord('a') + 13) % 26 + ord('a'))
    phonetics = ''.join([rot13(i) for i in phonetics])
    say(phonetics)

def say_all():
    for phonetic in sorted(phonetizer.phonetics.keys()):
        if phonetic == '0': continue
        print(phonetic)
        for i in range(4):
            say(f'[{phonetic}]')
            time.sleep(0.5)

def test():
    phonetics = [i for i in phonetizer.phonetics.keys() if i != '0']
    random.shuffle(phonetics)
    answers = []
    for phonetic in phonetics:
        for i in range(3):
            say(f'[{phonetic}]')
            if i != 2: time.sleep(0.5)
        print('what phonetic?')
        answers.append(input())
    for phonetic, answer in zip(phonetics, answers):
        print(phonetic, answer, '' if phonetic == answer else 'X')

if args.approach == 'sub':
    tone.midi([0x90, 42, 127])
    noise.midi([0x90, 60, 13])
else:
    tone.spectrum([])
    tone.midi([0x90, 42, 127])

dlal.typical_setup()
if args.phonetics or type(args.tell_story) == int:
    tape.to_file_i16le_start()
    if args.phonetics:
        if args.rot13:
            say_rot13(args.phonetics)
        else:
            say(args.phonetics)
    if type(args.tell_story) == int:
        tell_story(args.tell_story)
    tape.to_file_i16le_stop()
elif args.create_phonetic_samples:
    phonetics = [
        'ae', 'ay', 'a', 'e', 'y', 'i', 'o', 'w', 'uu', 'u',
        'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z', 'm', 'n', 'ng', 'r', 'l',
        'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
    ]
    os.makedirs('assets/local/phonetics', exist_ok=True)
    say_one('0')
    time.sleep(1)
    tape.clear()
    for phonetic in phonetics:
        say_one(phonetic)
        say_one('0')
        time.sleep(1)
        x = tape.read()
        sound = dlal.sound.Sound(x, SAMPLE_RATE)
        sound.to_flac(f'assets/local/phonetics/{phonetic}.flac')
        print(phonetic)
        time.sleep(1)
        tape.read()
