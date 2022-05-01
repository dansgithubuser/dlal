import dlal

import time

audio = dlal.Audio()
tape = dlal.Tape(1 << 17)

audio.add(audio)
audio.add(tape)

audio.connect(tape)

dlal.typical_setup()
tape.to_file_i16le_start('phonetics.i16le', 1 << 14)

phonetics = [
    'a as in apple',
    'a as in day',
    'a as in aw',
    'e as in bed',
    'e as in eat',
    'i as in it',
    'o as in oh',
    'oo as in zoo',
    'oo as in foot',
    'u as in uh',

    'sh as in shock',
    's as in fusion',
    'h as in heel',
    'f as in foot',
    'v as in vine',
    'th as in thin',
    'th as in the',
    's as in soon',
    'z as in zoo',
    'm as in map',
    'n as in nap',
    'ng as in thing',
    'r as in run',
    'l as in left',

    'p as in pine (repeat)',
    'b as in bin (repeat)',
    't as in tag (repeat)',
    'd as in day (repeat)',
    'k as in cook (repeat)',
    'g as in go (repeat)',
    'ch as in choose (repeat)',
    'j as in jog (repeat)',
]
for i in phonetics:
    print(f'breathe, prep {i}')
    time.sleep(dlal.speech.RECORD_DURATION_PREP)
    print('go')
    time.sleep(dlal.speech.RECORD_DURATION_GO)
    print('stop')
    time.sleep(dlals.speech.RECORD_DURATION_STOP)

tape.to_file_i16le_stop()
dlal.sound.i16le_to_flac('phonetics.i16le')
