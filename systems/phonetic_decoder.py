#===== imports =====#
import dlal

import argparse

#===== args =====#
parser = argparse.ArgumentParser()
parser.add_argument('--eval', '-e')
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

#===== main =====#
model = dlal.speech.Model('assets/local/phonetic-model.json')
run_size = audio.run_size()
sample_rate = audio.sample_rate()

phonetics_fusion = [
    'f', 'y', 'w', 'sh_v', 'i', 'n', '0',
    'h', 'y', 'w', 'm', 'r',
    'i', 'z',
    's', '0', 'o', 'w',
    'm', 'e', '0', 's', '0', 'y', '0',
    '0',
]
timings_fusion = [
    0.08, 0.14, 0.19, 0.24, 0.35, 0.39, 0.44,
    0.46, 0.55, 0.59, 0.63, 0.71,
    0.81, 0.88,
    0.92, 1.05, 1.08, 1.13,
    1.18, 1.26, 1.36, 1.37, 1.50, 1.52, 1.64,
    1.67,
]

phonetics_cat = [
    'h', 'ae', 'w', '0',
    'd', 'u', 'z',
    'th_v', 'u', '0',
    'g', 'r', 'ay', 'y', '0', 't', '0',
    'b', 'l', 'uu', 'w', '0',
    'k', 'ae', '0', 't', '0',
    'j', 'u', 'm', '0', 'p', '0',
    'j', 'ae', 'y', 'v', '0',
    'ae', 'n', 'd', '0',
    'd', 'ae', 'n', 's', '0',
    'e', 'f', 'r', 't', 'l', 'e', 's', 'l', 'y', '0',
    '0',
]
timings_cat = [
    0.10, 0.20, 0.30, 0.38,
    0.48, 0.49, 0.60,
    0.67, 0.74, 0.77,
    0.88, 0.92, 1.00, 1.04, 1.15, 1.20, 1.34,
    1.48, 1.49, 1.57, 1.66, 1.75,
    1.92, 2.03, 2.20, 2.29, 2.40,
    2.49, 2.56, 2.66, 2.73, 2.76, 2.89,
    2.99, 3.05, 3.19, 3.31, 3.38,
    3.43, 3.49, 3.55, 3.57,
    3.66, 3.69, 3.87, 3.94, 4.06,
    4.17, 4.27, 4.41, 4.46, 4.48, 4.58, 4.65, 4.84, 4.88, 4.99,
    5.05,
]

def say_one(phonetic, wait=None):
    info = model.phonetics[phonetic]
    frames = info['frames']
    if wait == None:
        wait = len(frames) * run_size
    for frame in frames:
        w = run_size
        if info['type'] == 'continuant':
            w = wait
        synth.synthesize(
            toniness=frame['toniness'],
            tone_formants=frame['tone']['formants'],
            noise_spectrum=frame['noise']['spectrum'],
            wait=w,
        )
        wait -= w
        if wait < 0: return
    if info['type'] == 'stop' and w > 0:
        say_one('0', wait)

def say_all(phonetics, timings):
    phonetics.insert(0, '0')
    timing_last = 0
    for phonetic, timing in zip(phonetics, timings):
        say_one(phonetic, int((timing - timing_last) * sample_rate))
        timing_last = timing

def say(*args, **kwargs):
    if type(args[0]) == str:
        say_one(*args, **kwargs)
    elif type(args[0]) == list:
        say_all(*args, **kwargs)
    else:
        raise Exception('Bad first argument.')

if args.eval:
    eval(args.eval)

dlal.typical_setup()
