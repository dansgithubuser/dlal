import dlal

import json
import math
import time

# consts
SAMPLE_RATE = 44100
STFT_BINS = 512
C = 1 / SAMPLE_RATE * STFT_BINS

NOISE_L_BIN_RANGE = [2000, 4000]
NOISE_M_BIN_RANGE = [4000, 8000]
NOISE_H_BIN_RANGE = [8000, 16000]

# components
audio = dlal.Audio(driver=True)
comm = dlal.Comm()

sinbank = dlal.Sinbank(44100 / 512)
noisebank = dlal.Noisebank()
gain_tone = dlal.Gain(name='gain_tone')
gain_noise = dlal.Gain(name='gain_noise')
mul = dlal.Mul(1)
buf_tone = dlal.Buf(name='buf_tone')
buf_noise = dlal.Buf(name='buf_noise')

buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

# connect
dlal.connect(
    (gain_tone, gain_noise),
    (buf_tone, buf_noise),
    [],
    mul,
    [buf_tone, buf_noise],
    [],
    (sinbank, noisebank),
    (buf_tone, buf_noise),
    buf,
    [audio, tape],
)

# phonetics
with open('assets/phonetics/simple.json') as f:
    model = json.loads(f.read())

def say_one(params):
    spectrum_tone = [0] * 256
    spectrum_noise = [0] * 64
    def add_tone(bin_i, bin_w, amp):
        for i in range(max(0, bin_i - bin_w), bin_i + bin_w):
            spectrum_tone[i] += amp
    def add_noise(f_i, f_f, amp):
        bin_i = int(f_i / (SAMPLE_RATE / 2) * 64)
        bin_f = int(f_f / (SAMPLE_RATE / 2) * 64)
        for i in range(bin_i, bin_f):
            spectrum_noise[i] += amp
    add_tone(round(params['f0_freq'][0] * C), 2, params['f0_amp'][0])
    add_tone(round(params['f1_freq'][0] * C), 2, params['f1_amp'][0])
    add_tone(round(params['f2_freq'][0] * C), 2, params['f2_amp'][0])
    add_tone(round(params['f3_freq'][0] * C), 2, params['f3_amp'][0])
    add_noise(*NOISE_L_BIN_RANGE, params['noise_l'][0])
    add_noise(*NOISE_M_BIN_RANGE, params['noise_m'][0])
    add_noise(*NOISE_H_BIN_RANGE, params['noise_h'][0])
    with dlal.Detach():
        sinbank.spectrum(spectrum_tone)
        noisebank.spectrum(spectrum_noise)
        gain_tone.set(params['amp_tone'][0])
        gain_noise.set(params['amp_noise'][0])

def say_all():
    for phonetic, label in model['labels'].items():
        print(phonetic)
        say_one(model['params'][label])
        time.sleep(1)

def say_with_transient(phonetic):
    a = model[say_with_transient.current]
    b = model[phonetic]
    n = 20
    for i in range(n):
        params = {
            k: [a[k][0] * (1 - i / n) + b[k][0] * (i / n), 0]
            for k in a.keys()
        }
        say_one(params)
        time.sleep(0.001)
    say_with_transient.current = phonetic
say_with_transient.current = '0'

def say(phonetics):
    phonetics += '0'
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
        say_with_transient(phonetic)
        time.sleep(0.25)

# command
sinbank.midi([0x90, 41, 0x40])
gain_tone.set(0)
gain_noise.set(0)

dlal.typical_setup()
