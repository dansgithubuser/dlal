#===== imports =====#
import dlal

import argparse
import random
import re
import time

#===== args =====#
parser = argparse.ArgumentParser(description=
    'Takes phonetic parameters as produced by phonetic_encoder.py, '
    'and synthesizes a sound.'
)
parser.add_argument('--phonetics-path', default='assets/phonetics')
args = parser.parse_args()

#===== system =====#
audio = dlal.Audio(driver=True)
comm = dlal.Comm()
synth = dlal.subsystem.SpeechSynth()
tape = dlal.Tape(44100*5)

dlal.connect(
    synth,
    [audio, tape],
)

phonetizer = dlal.speech.Phonetizer(synth.synthesize)

#===== main =====#
def say_code(code):
    phonetizer.say_code(code)

def say(code_string):
    phonetizer.say_code_string(code_string)

def say_all():
    for phonetic in phonetizer.model.keys():
        if phonetic == '0': continue
        print(phonetic)
        for i in range(3):
            say_code(phonetic)
            time.sleep(0.5)
            say_code('0')
            time.sleep(0.5)

def say_sentence(i):
    if i == 0 or 'ashes':
        d = 6400
        phonetizer.say_syllables(
            '.[ae].[sh] .i.z f.a.l [th]r.w [th_v][uu]m.y n.y.[ng]',
            [
                { 'on':  2 * d, 'off':  4 * d},
                { 'on':  4 * d, 'off':  6 * d},
                { 'on':  6 * d, 'off':  8 * d },
                { 'on':  8 * d, 'off': 10 * d },
                { 'on': 10 * d, 'off': 12 * d },
                { 'on': 12 * d, 'off': 14 * d },
            ],
        )

def test():
    phonetics = phonetizer.model.keys()
    random.shuffle(phonetics)
    answers = []
    for phonetic in phonetics:
        if phonetic == '0': continue
        for i in range(3):
            say_code(phonetic)
            time.sleep(0.5)
            say_code('0')
            if i != 2: time.sleep(0.5)
        print('what phonetic?')
        answers.append(input())
    for phonetic, answer in zip(phonetics, answers):
        print(phonetic, answer, '' if phonetic == answer else 'X')

synth.tone.midi([0x90, 42, 127])

dlal.typical_setup()
phonetizer.say_code('0')
