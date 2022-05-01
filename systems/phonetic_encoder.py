import dlal

import argparse
import os

try:
    import dansplotcore as dpc
except:
    pass

parser = argparse.ArgumentParser()
parser.add_argument('recording_path', nargs='?', default='assets/phonetics/phonetics.flac')
args = parser.parse_args()

# components
audio = dlal.Audio(driver=True)
filea = dlal.Filea(args.recording_path)
sampler = dlal.subsystem.SpeechSampler()

# connect
dlal.connect(
    filea,
    sampler,
)

# model
model = dlal.speech.Model()
assert audio.sample_rate() == model.sample_rate

# run
print('===== SAMPLING =====')
sampleses = sampler.sampleses_from_driver(audio)
print('===== MODELING =====')
for phonetic, samples in zip(dlal.speech.PHONETICS, sampleses):
    print(phonetic)
    model.add(phonetic, samples)
model.add_0()
model.save('assets/local/phonetic-model.json')
