import glob
import json
import os

import dansplotcore as dpc

phonetics = {}
for file_name in glob.glob('assets/phonetics/*.json'):
    with open(file_name) as file:
        name = os.path.basename(file_name).split('.')[0]
        phonetics[name] = json.loads(file.read())
plot = dpc.Plot()
for name, phonetic in phonetics.items():
    if name == '0': continue
    color = (192, 192, 192)
    toniness = phonetic['meta']['toniness']
    if toniness['voiced']: color = (255, 0, 0)
    plot.text(name, toniness['chaos'], toniness['tone'], *color)
plot.show()
