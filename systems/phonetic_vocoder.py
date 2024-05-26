import dlal

import argparse
import collections
import glob
import json
import math
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('recording_glob')
parser.add_argument('--visualize', '-v', action='store_true')
parser.add_argument('--noise-only', action='store_true')
parser.add_argument('--amp-plot', action='store_true')
parser.add_argument('--formants', '-f', action='store_true')
parser.add_argument('--noise-pieces', action='store_true')
parser.add_argument('--output-dir', '-o')
args = parser.parse_args()

recording_paths = sorted(glob.glob(args.recording_glob))

# components
audio = dlal.Audio(driver=True)
afr = dlal.Afr()
sampler = dlal.speech.SpeechSampler()
synth = dlal.speech.SpeechSynth()
tape = dlal.Tape()

# connect
dlal.connect(
    afr,
    sampler,
    [],
    synth,
    tape,
)

# commands
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
        # formants
        for formant_i in range(len(dlal.speech.FORMANT_RANGES)):
            for i, (a, b) in enumerate(zip(self.paramses, self.paramses[1:])):
                yi = a['tone']['formants'][formant_i]['freq']
                yf = b['tone']['formants'][formant_i]['freq']
                dy_a = 100 * log(a['tone']['formants'][formant_i]['amp'], 3)
                dy_b = 100 * log(b['tone']['formants'][formant_i]['amp'], 3)
                kwargs = dict(
                    xi=i,
                    xf=i+1,
                    r=1.0,
                    b=0.0,
                )
                plot.line(yi=yi, yf=yf, g=0.5, **kwargs)
                plot.line(yi=yi+dy_a, yf=yf+dy_b, g=0, **kwargs)
                plot.line(yi=yi-dy_a, yf=yf-dy_b, g=0, **kwargs)
        # toniness
        plot.plot([(i['toniness']-1) * 100 for i in self.paramses])
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
for recording_path in recording_paths:
    print(recording_path)
    afr.open(recording_path)
    duration = afr.duration()
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
        if args.noise_pieces:
            noise_params = {'noise_pieces': frame['noise']['pieces']}
        else:
            noise_params = {'noise_spectrum': frame['noise']['spectrum']}
        synth.synthesize(
            toniness=frame['toniness'],
            wait=0,
            **tone_params,
            **noise_params,
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

    file.close()
    if args.output_dir:
        path = Path(args.output_dir) / Path(recording_path).with_suffix('.flac').name
        dlal.sound.i16le_to_flac(file.name, path)

    if args.amp_plot:
        import dansplotcore as dpc
        plot = dpc.Plot(primitive=dpc.primitives.Line())
        for i, (k, v) in enumerate(amps.items()):
            plot.text(k, **plot.transform(0, -(i+1)/5, i, plot.series))
            plot.plot(v)
        plot.show()
