import dlal

import argparse
import json
import math
import os

parser = argparse.ArgumentParser()
parser.add_argument('recording_path')
parser.add_argument('--visualize', '-v', action='store_true')
args = parser.parse_args()

# components
audio = dlal.Audio(driver=True)
filea = dlal.Filea(args.recording_path)
sampler = dlal.subsystem.SpeechSampler()
synth = dlal.subsystem.SpeechSynth()
tape = dlal.Tape()

# connect
dlal.connect(
    filea,
    sampler,
    [],
    synth,
    tape,
)

# commands
duration = filea.duration()
run_size = audio.run_size()

# model
model = dlal.speech.Model()
assert audio.sample_rate() == model.sample_rate
assert audio.run_size() == model.run_size

# visualizer
class Visualizer:
    def __init__(self):
        self.sampleses = []
        self.paramses = []
        self.amps = []

    def add(self, sample, params, amp):
        if not args.visualize: return
        self.sampleses.append(sample)
        self.paramses.append(params)
        self.amps.append(amp)

    def show(self):
        if not args.visualize: return
        import dansplotcore as dpc
        plot = dpc.Plot(
            transform=dpc.transforms.Default('w'),
            primitive=dpc.primitives.Line(),
        )
        def log(x, e=4):
            if x < 10 ** -e: return 0
            return (math.log10(x) + e) / e
        # spectrogram
        amp_max = max(max(spectrum) for spectrum, _, _ in self.sampleses)
        for samples_i, (spectrum, _, _) in enumerate(self.sampleses):
            for bin_i, amp in enumerate(spectrum):
                amp_n = amp / amp_max
                if amp_n < 1e-4: continue
                plot.rect(
                    samples_i+0,
                    (bin_i+0) * model.freq_per_bin,
                    samples_i+1,
                    (bin_i+1) * model.freq_per_bin,
                    a=log(amp_n),
                )
        # formants and freq_c
        for formant_i in range(len(dlal.speech.FORMANT_RANGES)):
            for i, (a, b) in enumerate(zip(self.paramses, self.paramses[1:])):
                plot.line(
                    i,
                    a['tone']['formants'][formant_i]['freq'],
                    i+1,
                    b['tone']['formants'][formant_i]['freq'],
                    r=1.0,
                    g=log(a['tone']['formants'][formant_i]['amp'], 2),
                    b=0.0,
                )
                plot.line(
                    i,
                    a['noise']['freq_c'],
                    i+1,
                    b['noise']['freq_c'],
                    r=0.0,
                )
        # toniness
        plot.plot([(i['toniness']-1) * 100 for i in self.paramses])
        # noise hi
        plot.plot([(i['noise']['hi']-3) * 100 for i in self.paramses])
        # f
        plot.plot([(i['f']-5) * 100 for i in self.paramses])
        #
        plot.show()

visualizer = Visualizer()

# run
samples = 0
file = open('phonetic_vocoder.i16le', 'wb')
while samples < duration:
    audio.run()
    sample = sampler.sample()
    params = model.parameterize(*sample)
    frame = model.frames_from_paramses([params])[0]
    amp = min(params['f'] * 10, 1)
    visualizer.add(sample, params, amp)
    synth.synthesize(
        [amp * i for i in frame['tone']['spectrum']],
        [amp * i for i in frame['noise']['spectrum']],
        frame['toniness'],
        0,
    )
    tape.to_file_i16le(file)
    samples += run_size
    print('{:>6.2f}%'.format(100 * samples / duration), end='\r')
print()
visualizer.show()
