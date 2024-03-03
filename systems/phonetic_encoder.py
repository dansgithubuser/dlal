import dlal

import argparse
import json
import os

try:
    import dansplotcore as dpc
except:
    pass

parser = argparse.ArgumentParser()
parser.add_argument('recordings_path', nargs='?', default='assets/phonetics')
args = parser.parse_args()

# components
audio = dlal.Audio(driver=True)
filea = dlal.Filea()
sampler = dlal.speech.SpeechSampler()

# connect
dlal.connect(
    filea,
    sampler,
)

# model
model = dlal.speech.Model()
assert audio.sample_rate() == model.sample_rate
assert audio.run_size() == model.run_size

# run
print('===== SAMPLING =====')
sampleses = sampler.sampleses(args.recordings_path, filea, audio)

print('===== MODELING =====')
for k, samples in sampleses.items():
    print(k)
    if k in dlal.speech.PHONETICS:
        model.add(k, samples)
    elif k in dlal.speech.VOICED_STOP_CONTEXTS:
        model.add_voiced_stop_context(k, samples)
model.add_0()
model.save('assets/local/phonetic-model.json')
model.save_formant_path_plot_data('assets/local/formant-paths.json')

print('===== DUMPING MEAN SPECTRA =====')
mean_spectra = {}
for k, samples in sampleses.items():
    print(k)
    mean_spectrum = [0] * len(samples[0][0])
    if k in dlal.speech.VOICED and k not in dlal.speech.STOPS:
        irrelevant = dlal.speech.RECORD_DURATION_UNSTRESSED_VOWEL + dlal.speech.RECORD_DURATION_TRANSITION + 1
        total = irrelevant + dlal.speech.RECORD_DURATION_GO - 1
        start = int(len(samples) * irrelevant / total)
        samples = samples[start:]
    for (spectrum, _, _) in samples:
        for i in range(len(mean_spectrum)):
            mean_spectrum[i] += spectrum[i]
    for i in range(len(mean_spectrum)):
        mean_spectrum[i] /= len(samples)
    mean_spectra[k] = mean_spectrum
with open('assets/local/mean-spectra.json', 'w') as f:
    json.dump(mean_spectra, f, indent=2)
