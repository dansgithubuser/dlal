#===== imports =====#
from system import MonitorSys

import dlal

import dansplotcore as dpc

import json
from pathlib import Path

#===== init =====#
monitor_sys = MonitorSys()

#===== helpers =====#
def sample(name):
    monitor_sys.monitor.sample(name)

def save(path='monitor.json'):
    j = monitor_sys.monitor.to_json()
    with open(path, 'w') as f: json.dump(j, f, indent=2)

def load(path='monitor.json'):
    with open(path) as f: j = json.load(f)
    monitor_sys.monitor.from_json(j)

def plot():
    plot = dpc.Plot(primitive=dpc.p.Line())
    categories = monitor_sys.monitor.categories()
    for name, category in categories.items():
        plot.plot(category, legend=name)
    plot.show()

#===== run =====#
if Path('monitor.json').exists():
    load('monitor.json')
monitor_sys.start()
monitor_sys.start_db()
