import dlal

import argparse
import json
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

print('===== DUMPING MEAN SPECTRA =====')
mean_spectra = {}
for phonetic, samples in zip(dlal.speech.PHONETICS, sampleses):
    print(phonetic)
    mean_spectrum = [0] * len(samples[0][0])
    for (spectrum, _, _) in samples:
        for i in range(len(mean_spectrum)):
            mean_spectrum[i] += spectrum[i]
    for i in range(len(mean_spectrum)):
        mean_spectrum[i] /= len(samples)
    mean_spectra[phonetic] = mean_spectrum
with open('assets/local/mean-spectra.json', 'w') as f:
    json.dump(mean_spectra, f, indent=2)
