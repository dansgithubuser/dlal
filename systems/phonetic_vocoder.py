import dlal

import argparse
import collections
import json
import math
import os

parser = argparse.ArgumentParser()
parser.add_argument('recording_path')
parser.add_argument('--visualize', '-v', action='store_true')
parser.add_argument('--noise-only', action='store_true')
parser.add_argument('--amp-plot', action='store_true')
parser.add_argument('--formants', action='store_true')
parser.add_argument('--noise-controller', action='store_true')
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

    def add(self, sample, params):
        if not args.visualize: return
        self.sampleses.append(sample)
        self.paramses.append(params)

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

# amp plot
if args.amp_plot:
    peak_rec = dlal.Peak()
    peak_synth_full = dlal.Peak()
    peak_synth_tone = dlal.Peak()
    peak_synth_noise = dlal.Peak()
    sampler.buf.connect(peak_rec)
    synth.buf_tone.connect(peak_synth_tone)
    synth.buf_noise.connect(peak_synth_noise)
    synth.buf_out.connect(peak_synth_full)
    amps = collections.defaultdict(list)

    def amp_spectrum(spectrum):
        return sum(spectrum[1:])

# run
samples = 0
file = open('phonetic_vocoder.i16le', 'wb')
formants_prev = None
while samples < duration:
    audio.run()
    sample = sampler.sample()
    params = model.parameterize(*sample, 's' if args.noise_only else None, formants_prev=formants_prev)
    formants_prev = params['tone']['formants']
    frame = model.frames_from_paramses([params])[0]
    visualizer.add(sample, params)
    if args.formants:
        tone_params = {'tone_formants': frame['tone']['formants']}
    else:
        tone_params = {'tone_spectrum': frame['tone']['spectrum']}
    if args.noise_controller:
        noise_spectrum = model.noise_controller.predict(
            frame['toniness'],
            frame['noise']['freq_c'],
            frame['noise']['hi'],
        )
    else:
        noise_spectrum = frame['noise']['spectrum']
    synth.synthesize(
        toniness=frame['toniness'],
        noise_spectrum=noise_spectrum,
        wait=0,
        **tone_params,
    )
    tape.to_file_i16le(file)
    samples += run_size
    print('{:>6.2f}%'.format(100 * samples / duration), end='\r')
    if args.amp_plot:
        amps['rec'].append(peak_rec.value())
        amps['stft'].append(amp_spectrum(sample[0]))
        amps['tone'].append(amp_spectrum(params['tone']['spectrum']))
        amps['noise'].append(amp_spectrum(params['noise']['spectrum']))
        amps['synth_tone'].append(peak_synth_tone.value())
        amps['synth_noise'].append(peak_synth_noise.value())
        amps['synth_full'].append(peak_synth_full.value())
print()
visualizer.show()

if args.amp_plot:
    import dansplotcore as dpc
    plot = dpc.Plot(primitive=dpc.primitives.Line())
    for i, (k, v) in enumerate(amps.items()):
        plot.text(k, **plot.transform(0, -(i+1)/5, i, plot.series))
        plot.plot(v)
    plot.show()
