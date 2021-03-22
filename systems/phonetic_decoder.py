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
parser.add_argument('--tell-story', type=int)
args = parser.parse_args()

#===== consts =====#
SAMPLE_RATE = 44100

#===== system =====#
audio = dlal.Audio()
dlal.driver_set(audio)
comm = dlal.Comm()
vibrato = dlal.subsystem.Vibrato()
tone = dlal.Train(name='tone')
noise = dlal.Osc('noise', name='noise')
phonetizer = dlal.subsystem.Phonetizer()
tape = dlal.Tape(size=44100*5)

dlal.connect(
    (vibrato),
    (tone, noise),
    (phonetizer.tone_buf, phonetizer.noise_buf),
    [],
    phonetizer,
    [audio, tape],
)

#===== main =====#
def say_one(phonetic):
    if phonetic == ' ':
        phonetic = '0'
    time.sleep(phonetizer.say(phonetic) / 44100)

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
        '[[ae]yh[ae]vuf[ae]nsysilwet]',
        # 8
        '[h[ae]wduz[th_v]ugreytblwk[ae]tjumpjayv[ae]nd[ae]nsefrtlesly]',
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
            'hipow',
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
            'vyikl', 'vwvwzeylu',
            'w[uu]min',
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

tone.midi([0x90, 42, 0x7f])
noise.midi([0x90, 60, 0x40])
dlal.typical_setup()
if args.phonetics or type(args.tell_story) == int:
    tape.to_file_i16le_start()
    if args.phonetics:
        say(args.phonetics)
    if type(args.tell_story) == int:
        tell_story(args.tell_story)
    tape.to_file_i16le_stop()
