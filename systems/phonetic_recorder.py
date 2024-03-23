#===== imports =====#
import dlal

import argparse
import os
import time

#===== args =====#
parser = argparse.ArgumentParser()
parser.add_argument('--only-unrecorded', action='store_true')
args = parser.parse_args()

#===== components ======#
audio = dlal.Audio(driver=True)
audio.add(audio)
tape = dlal.Tape(1 << 17)

#===== connect =====#
audio.connect(tape)

#===== main =====#
dlal.typical_setup()

dur_2 = dlal.speech.RECORD_DURATION_UNSTRESSED_VOWEL
dur_1 = dlal.speech.RECORD_DURATION_TRANSITION
dur = dlal.speech.RECORD_DURATION_GO

print('Make sure you are comfortable so you can record each phonetic in a similar posture, body & mic position, etc.')
print('Make sure mic volume is good.')
print('Press enter to continue.')
input()

print('(1/4) Voiced continuants will be recorded.')
print('For each phonetic:')
print('- you will get a 3, 2, 1 countdown, start on 1 in anticipation of the start of the recording')
print(f'- start with about {dur_2} seconds of unstressed vowel sound')
print(f'- slowly change to the phonetic over about {dur_1} seconds')
print(f'- record about {dur} seconds of the phonetic, wait for "Done!" before stopping.')
print('Press enter to continue.')
input()
phonetic_i = 0
while phonetic_i < len(dlal.speech.PHONETICS):
    phonetic = dlal.speech.PHONETICS[phonetic_i]
    if phonetic not in dlal.speech.VOICED:
        phonetic_i += 1
        continue
    if phonetic in dlal.speech.STOPS:
        phonetic_i += 1
        continue
    if args.only_unrecorded and os.path.exists(f'assets/phonetics/{phonetic}.flac'):
        phonetic_i += 1
        continue
    print()
    print(f'Recording voiced continuant [{phonetic}].')
    print(dlal.speech.PHONETIC_DESCRIPTIONS[phonetic])
    print('When you are ready, press enter.')
    input()
    for i in [3, 2, 1]:
        print(i)
        time.sleep(1)
    tape.to_file_i16le_start('assets/local/tmp.i16le', 1 << 14)
    print(f'- start with about {dur_2} seconds of unstressed vowel sound')
    time.sleep(dur_2)
    print(f'- slowly change to the phonetic over about {dur_1} seconds')
    time.sleep(dur_1)
    print(f'- record about {dur} seconds of the phonetic, wait for "Done!" before stopping.')
    time.sleep(dur)
    tape.to_file_i16le_stop()
    dlal.sound.i16le_to_flac('assets/local/tmp.i16le', f'assets/phonetics/{phonetic}.flac')
    print('Done!')
    print('Want to repeat this phonetic? Enter y for yes, enter anything else for no.')
    if input() != 'y':
        phonetic_i += 1
    else:
        os.remove(f'assets/phonetics/{phonetic}.flac')

print('(2/4) Unvoiced continuants will be recorded.')
print('For each phonetic:')
print('- you will get a 3, 2, 1 countdown, start on 1 in anticipation of the start of the recording')
print(f'- record about {dur} seconds of the phonetic, wait for "Done!" before stopping.')
print('Press enter to continue.')
input()
phonetic_i = 0
while phonetic_i < len(dlal.speech.PHONETICS):
    phonetic = dlal.speech.PHONETICS[phonetic_i]
    if phonetic in dlal.speech.VOICED:
        phonetic_i += 1
        continue
    if phonetic in dlal.speech.STOPS:
        phonetic_i += 1
        continue
    if args.only_unrecorded and os.path.exists(f'assets/phonetics/{phonetic}.flac'):
        phonetic_i += 1
        continue
    print()
    print(f'Recording unvoiced continuant [{phonetic}].')
    print(dlal.speech.PHONETIC_DESCRIPTIONS[phonetic])
    print('When you are ready, press enter.')
    input()
    for i in [3, 2, 1]:
        print(i)
        time.sleep(1)
    tape.to_file_i16le_start('assets/local/tmp.i16le', 1 << 14)
    print(f'- record about {dur} seconds of the phonetic, wait for "Done!" before stopping.')
    time.sleep(dur)
    tape.to_file_i16le_stop()
    dlal.sound.i16le_to_flac('assets/local/tmp.i16le', f'assets/phonetics/{phonetic}.flac')
    print('Done!')
    print('Want to repeat this phonetic? Enter y for yes, enter anything else for no.')
    if input() != 'y':
        phonetic_i += 1
    else:
        os.remove(f'assets/phonetics/{phonetic}.flac')

print('(3/4) Unvoiced stops will be recorded.')
print('For each phonetic:')
print('- you will get a 3, 2, 1 countdown')
print('- repeat the stop')
print('- do not anticipate; start after the instruction to record')
print('- speak as if you were following the stop with an unstressed vowel')
print('- do not voice anything, speak in a loud whisper')
print(f'- record about {dur} seconds of the phonetic, wait for "Done!" before stopping.')
print('Press enter to continue.')
input()
phonetic_i = 0
while phonetic_i < len(dlal.speech.PHONETICS):
    phonetic = dlal.speech.PHONETICS[phonetic_i]
    if phonetic in dlal.speech.VOICED:
        phonetic_i += 1
        continue
    if phonetic not in dlal.speech.STOPS:
        phonetic_i += 1
        continue
    if args.only_unrecorded and os.path.exists(f'assets/phonetics/{phonetic}.flac'):
        phonetic_i += 1
        continue
    print()
    print(f'Recording stop [{phonetic}]. Say [{phonetic}u{phonetic}].')
    print(dlal.speech.PHONETIC_DESCRIPTIONS[phonetic])
    print('When you are ready, press enter.')
    input()
    for i in [3, 2, 1]:
        print(i)
        time.sleep(1)
    tape.to_file_i16le_start('assets/local/tmp.i16le', 1 << 14)
    print(f'- record about {dur} seconds of the phonetic, wait for "Done!" before stopping.')
    time.sleep(dur)
    tape.to_file_i16le_stop()
    dlal.sound.i16le_to_flac('assets/local/tmp.i16le', f'assets/phonetics/{phonetic}.flac')
    print('Done!')
    print('Want to repeat this phonetic? Enter y for yes, enter anything else for no.')
    if input() != 'y':
        phonetic_i += 1
    else:
        os.remove(f'assets/phonetics/{phonetic}.flac')

print('(4/4) Voiced stops will be recorded.')
print('For each phonetic:')
print('- you will get a 3, 2, 1 countdown')
print('- overall, as if it were a word, say the stop, followed by the unstressed vowel, followed by the stop')
print('- the entire recording will be {3 * dur_2} seconds')
print('- the 1st third should completely contain the first saying of the stop')
print('- the 2nd third should only be unstressed vowel')
print('- the 3rd third should completely contain the last saying of the stop')
print('Press enter to continue.')
input()
phonetic_i = 0
while phonetic_i < len(dlal.speech.PHONETICS):
    phonetic = dlal.speech.PHONETICS[phonetic_i]
    if phonetic not in dlal.speech.VOICED:
        phonetic_i += 1
        continue
    if phonetic not in dlal.speech.STOPS:
        phonetic_i += 1
        continue
    if args.only_unrecorded and os.path.exists(f'assets/phonetics/{phonetic}.flac'):
        phonetic_i += 1
        continue
    print()
    print(f'Recording voiced stop [{phonetic}].')
    print(f'Say [{phonetic}u{phonetic}] for about {3 * dur_2} seconds, wait for "Done!" before stopping.')
    print('When you are ready, press enter.')
    input()
    for i in [3, 2, 1]:
        print(i)
        time.sleep(1)
    tape.to_file_i16le_start('assets/local/tmp.i16le', 1 << 14)
    print('Go!')
    time.sleep(2 * dur_2)
    print('Done!')
    time.sleep(1 * dur_2)
    tape.to_file_i16le_stop()
    dlal.sound.i16le_to_flac('assets/local/tmp.i16le', f'assets/phonetics/{phonetic}.flac')
    print('Want to repeat this phonetic? Enter y for yes, enter anything else for no.')
    if input() != 'y':
        phonetic_i += 1
    else:
        os.remove(path)

print()
print('All done, congratulations!')
