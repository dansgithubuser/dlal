import dansplotcore as dpc
import dlal

import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('recording_path')
args = parser.parse_args()

os.environ['PHONETIC_ENCODER_RECORDING_PATH'] = args.recording_path
import phonetic_encoder as pe
dlal.comm_set(None)

run_size = pe.audio.run_size()
duration = pe.filea.duration()
samples = 0
features = []

while samples < duration:
    pe.audio.run()
    sample = pe.sample_system()
    params = pe.parameterize(*sample)
    features.append(dlal.speech.get_features(params))
    samples += run_size
    print(f'{samples} / {duration}', end='\r')
print()

plot = dpc.Plot(
    transform=dpc.transforms.Grid(duration // 64, 1, 1),
    primitive=dpc.primitives.Line(),
)
for i, feature in enumerate(dlal.speech.FEATURES):
    plot.text(feature, **plot.transform(0, 0, None, plot.series), r=1.0, g=0, b=0)
    plot.plot([j[i] for j in features])
plot.show()
